# app.py (Revised for Client-Side STT, CORS, Logging, AND VIDEO FRAMES)
import os
from dotenv import load_dotenv
import asyncio
import threading
from flask import Flask, render_template, request # Make sure request is imported
from flask_socketio import SocketIO, emit

load_dotenv()
from Cortex_Online import Cortex # Make sure filename matches Cortex_Online.py

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_default_fallback_secret_key!')

REACT_APP_PORT = os.getenv('REACT_APP_PORT', '5173')
REACT_APP_ORIGIN = f"http://localhost:{REACT_APP_PORT}"
REACT_APP_ORIGIN_IP = f"http://127.0.0.1:{REACT_APP_PORT}"

socketio = SocketIO(
    app,
    async_mode='threading',
    cors_allowed_origins=[REACT_APP_ORIGIN, REACT_APP_ORIGIN_IP]
)

Cortex_instance = None
Cortex_loop = None
Cortex_thread = None

def run_asyncio_loop(loop):
    """ Function to run the asyncio event loop in a separate thread """
    asyncio.set_event_loop(loop)
    try:
        print("Asyncio event loop started...")
        loop.run_forever()
    finally:
        print("Asyncio event loop stopping...")
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            if not task.done():
                task.cancel()
        try:
            loop.run_until_complete(asyncio.gather(*[t for t in tasks if not t.done()], return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
        except RuntimeError as e:
             print(f"RuntimeError during loop cleanup (might be expected if loop stopped abruptly): {e}")
        except Exception as e:
            print(f"Exception during loop cleanup: {e}")
        finally:
            if not loop.is_closed():
                loop.close()
        print("Asyncio event loop stopped.")

@socketio.on('connect')
def handle_connect():
    """ Handles new client connections """
    global Cortex_instance, Cortex_loop, Cortex_thread
    client_sid = request.sid
    print(f"\n--- handle_connect called for SID: {client_sid} ---")

    if Cortex_thread is None or not Cortex_thread.is_alive():
        print(f"    Asyncio thread not running. Starting new loop and thread.")
        Cortex_loop = asyncio.new_event_loop()
        Cortex_thread = threading.Thread(target=run_asyncio_loop, args=(Cortex_loop,), daemon=True)
        Cortex_thread.start()
        print("    Started asyncio thread.")
        socketio.sleep(0.1)

    if Cortex_instance is None:
        print(f"    Creating NEW Cortex instance for SID: {client_sid}")
        if not Cortex_loop or not Cortex_loop.is_running():
             print(f"    ERROR: Cannot create Cortex instance, asyncio loop not ready for SID {client_sid}.")
             emit('error', {'message': 'Assistant initialization error (loop).'}, room=client_sid)
             return

        try:
            Cortex_instance = Cortex(socketio_instance=socketio, client_sid=client_sid)
            future = asyncio.run_coroutine_threadsafe(Cortex_instance.start_all_tasks(), Cortex_loop)
            print("    Cortex instance created and tasks scheduled.")
        except ValueError as e:
            print(f"    ERROR initializing Cortex (ValueError) for SID {client_sid}: {e}")
            emit('error', {'message': f'Failed to initialize assistant: {e}'}, room=client_sid)
            Cortex_instance = None
            return
        except Exception as e:
            print(f"    ERROR initializing Cortex (Unexpected) for SID {client_sid}: {e}")
            emit('error', {'message': f'Unexpected error initializing assistant: {e}'}, room=client_sid)
            Cortex_instance = None
            return
    else:
        print(f"    Cortex instance already exists. Updating SID from {Cortex_instance.client_sid} to {client_sid}")
        Cortex_instance.client_sid = client_sid

    if Cortex_instance:
        emit('status', {'message': 'Connected to Cortex Assistant'}, room=client_sid)
    print(f"--- handle_connect finished for SID: {client_sid} ---\n")


@socketio.on('disconnect')
def handle_disconnect():
    """ Handles client disconnections """
    global Cortex_instance
    client_sid = request.sid
    print(f"\n--- handle_disconnect called for SID: {client_sid} ---")

    if Cortex_instance and Cortex_instance.client_sid == client_sid:
        print(f"    Designated client {client_sid} disconnected. Attempting to stop Cortex.")
        if Cortex_loop and Cortex_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(Cortex_instance.stop_all_tasks(), Cortex_loop)
            try:
                future.result(timeout=10)
                print("    Cortex tasks stopped successfully.")
            except TimeoutError:
                print("    Timeout waiting for Cortex tasks to stop.")
            except Exception as e:
                print(f"    Exception during Cortex task stop: {e}")
            finally:
                 pass # Keep loop running

        else:
             print(f"    Cannot stop Cortex tasks: asyncio loop not available or not running.")

        Cortex_instance = None
        print("    Cortex instance cleared.")

    elif Cortex_instance:
         print(f"    Disconnecting client {client_sid} is NOT the designated client ({Cortex_instance.client_sid}). Cortex remains active.")
    else:
         print(f"    Client {client_sid} disconnected, but no active Cortex instance found.")

    print(f"--- handle_disconnect finished for SID: {client_sid} ---\n")


@socketio.on('send_text_message')
def handle_text_message(data):
    """ Receives text message from client's input box """
    client_sid = request.sid
    message = data.get('message', '')
    print(f"Received text from {client_sid}: {message}")
    if Cortex_instance and Cortex_instance.client_sid == client_sid:
        if Cortex_loop and Cortex_loop.is_running():
            # Process text with end_of_turn=True implicitly handled in process_input -> run_gemini_session
            asyncio.run_coroutine_threadsafe(Cortex_instance.process_input(message, is_final_turn_input=True), Cortex_loop)
            print(f"    Text message forwarded to Cortex for SID: {client_sid}")
        else:
            print(f"    Cannot process text message for SID {client_sid}: asyncio loop not ready.")
            emit('error', {'message': 'Assistant busy or loop error.'}, room=client_sid)
    else:
        print(f"    Cortex instance not ready or SID mismatch for text message from {client_sid}.")
        emit('error', {'message': 'Assistant not ready or session mismatch.'}, room=client_sid)


@socketio.on('send_transcribed_text')
def handle_transcribed_text(data):
    """ Receives final transcribed text from client's Web Speech API """
    client_sid = request.sid
    transcript = data.get('transcript', '')
    print(f"Received transcript from {client_sid}: {transcript}")
    if transcript and Cortex_instance and Cortex_instance.client_sid == client_sid:
         if Cortex_loop and Cortex_loop.is_running():
            # Process transcript with end_of_turn=True implicitly handled in process_input -> run_gemini_session
            asyncio.run_coroutine_threadsafe(Cortex_instance.process_input(transcript, is_final_turn_input=True), Cortex_loop)
            print(f"    Transcript forwarded to Cortex for SID: {client_sid}")
         else:
             print(f"    Cannot process transcript for SID {client_sid}: asyncio loop not ready.")
             emit('error', {'message': 'Assistant busy or loop error.'}, room=client_sid)
    elif not transcript:
         print("    Received empty transcript.")
    else:
         print(f"    Cortex instance not ready or SID mismatch for transcript from {client_sid}.")


# **** ADD VIDEO FRAME HANDLER ****
@socketio.on('send_video_frame')
def handle_video_frame(data):
    """ Receives base64 video frame data from client """
    client_sid = request.sid
    frame_data_url = data.get('frame') # Expecting data URL like 'data:image/jpeg;base64,xxxxx'

    if frame_data_url and Cortex_instance and Cortex_instance.client_sid == client_sid:
        if Cortex_loop and Cortex_loop.is_running():
            print(f"Received video frame from {client_sid}, forwarding...") # Optional: very verbose
            asyncio.run_coroutine_threadsafe(Cortex_instance.process_video_frame(frame_data_url), Cortex_loop)
        pass

@socketio.on('video_feed_stopped')
def handle_video_feed_stopped():
    """ Client signaled that the video feed has stopped. """
    client_sid = request.sid
    print(f"Received video_feed_stopped signal from {client_sid}.")
    if Cortex_instance and Cortex_instance.client_sid == client_sid:
        if Cortex_loop and Cortex_loop.is_running():
            # Call a method on Cortex instance to clear its video queue
            asyncio.run_coroutine_threadsafe(Cortex_instance.clear_video_queue(), Cortex_loop)
            print(f"    Video frame queue clearing requested for SID: {client_sid}")
        else:
            print(f"    Cannot clear video queue for SID {client_sid}: asyncio loop not ready.")
    else:
        print(f"    Cortex instance not ready or SID mismatch for video_feed_stopped from {client_sid}.")


if __name__ == '__main__':
    print("Starting Flask-SocketIO server...")
    try:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    finally:
        print("\nServer shutting down...")
        if Cortex_instance:
             print("Attempting to stop active Cortex instance on server shutdown...")
             if Cortex_loop and Cortex_loop.is_running():
                 future = asyncio.run_coroutine_threadsafe(Cortex_instance.stop_all_tasks(), Cortex_loop)
                 try:
                     future.result(timeout=5)
                     print("Cortex tasks stopped.")
                 except TimeoutError:
                     print("Timeout stopping Cortex tasks during shutdown.")
                 except Exception as e:
                     print(f"Exception stopping Cortex tasks during shutdown: {e}")
             else:
                 print("Cannot stop Cortex instance: asyncio loop not available.")
             Cortex_instance = None

        if Cortex_loop and Cortex_loop.is_running():
             print("Stopping asyncio loop from main thread...")
             Cortex_loop.call_soon_threadsafe(Cortex_loop.stop)
             if Cortex_thread and Cortex_thread.is_alive():
                 Cortex_thread.join(timeout=5)
                 if Cortex_thread.is_alive():
                     print("Warning: Asyncio thread did not exit cleanly.")
             print("Asyncio loop/thread stop initiated.")
        print("Shutdown complete.")