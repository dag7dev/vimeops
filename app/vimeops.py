import os
from os.path import join, dirname
from dotenv import load_dotenv
import click
import vimeo
import json

# DEBUG
DEBUG = False

# Preliminary ops
# ---------------
# Loading dotenv env variables
dotenv_path = os.path.join(dirname(__file__), '.env.sample' if DEBUG else '.env') 
loaded = load_dotenv(dotenv_path)
if not loaded and DEBUG:
    click.echo("[WARN]: Failed to load the .env file.")
    
# Vimeo variables
CLIENT_ID = os.environ.get("CLIENT_ID") if "CLIENT_ID" in os.environ else ""
CLIENT_SECRET = os.environ.get("CLIENT_SECRET") if "CLIENT_SECRET" in os.environ else ""
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN") if "ACCESS_TOKEN" in os.environ else ""

# INPUT_DIR -> where videos are stored
# DOWNLOAD_DIR -> where videos WILL BE stored
INPUT_DIR = os.environ.get("INPUT_DIR") if "INPUT_DIR" in os.environ else ""
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR") if "DOWNLOAD_DIR" in os.environ else ""

THRESHOLD = os.environ.get("THRESHOLD") if "THRESHOLD" in os.environ else 10

# Logs: creating directories and json files
if not os.path.exists("app/logs"): os.mkdir("app/logs")
if not os.path.exists("app/logs/upload.json"): open('app/logs/upload.json', 'w')
if not os.path.exists("app/logs/download.json"): open('app/logs/download.json', 'w')


# UTILS
# -----
def connect_to_vimeo(client_id, client_secret, access_token):
    """Function to establish a connection with Vimeo servers."""
    try:
        # Vimeo client
        v = vimeo.VimeoClient(
            token=access_token,
            key=client_id,
            secret=client_secret
        )
        return v
    except Exception as e:
        click.echo(f"[ERR] Error connecting to Vimeo! Reason: {e}")
        raise click.Abort()


def upload_single_file(filepath, v):
    """
    Upload a single video, given his full path.
    Returns True if file has been uploaded, False if exception occurs
    """
    ret = False

    try:
        video_uri = v.upload(
            filepath,
            data={'name': filepath.split("/")[-1].split(".")[0]}
        )
        click.echo(" OK")
        ret = True
    except Exception as e:
        click.echo(f" ERROR! Reason: {e}")

    return ret
    

def get_all_videos(v):
    all_videos = []
    
    # Get the total video count from the initial response
    endpoint_call = v.get('/me/videos', params={'per_page': 100}).json()
    total_videos = endpoint_call['total']
    if DEBUG: print(f"[INFO] Total videos: {str(total_videos)}")

    # Calculate the total number of pages
    # Context: in a sample call it gives a reply like this one
    # {
    #   "total": 255,
    #   "page": 1,
    #   "per_page": 100,
    #   "paging": {
    #     ...
    #     "last": "/users/<>/videos?per_page=100&page=3"
    # }
    # So we can safely assume that page 3, in this case is the latest.
    total_pages = endpoint_call['paging']['last'].split('=')[-1]

    if DEBUG: print(f"[INFO] Total pages: {total_pages}")

    for page in range(1, int(total_pages) + 1):
        response = v.get('/me/videos', params={'per_page': 100, 'page': page})
        videos = response.json()['data']
        print(f"Getting page {str(page)}")
        all_videos += videos
    return all_videos

def download_video(v, video, path):
    ret = False
    video_data = video

    # Getting the download link
    download_links = video_data['download']
    download_link = next((link['link'] for link in download_links if link['quality'] == 'hd'), 
                        next((link['link'] for link in download_links if link['quality'] == 'sd'), None))

    # Download the video
    video_filename = video['name'] + ".mp4"

    try:
        with open(os.path.join(path, video_filename), 'wb') as f:
            response = v.get(download_link, stream=True)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        click.echo(" OK")

        ret = True
    except Exception as e:
        click.echo(f"ERROR! Reason: {e}")

    return ret

# MAIN
# ----
@click.group(context_settings=dict(max_content_width=1000)) # Help output will be truncated if context_settings is not defined 
@click.option('--suppress-confirmation', is_flag=True, default=False, help='Suppress the confirmation prompts. To be used in conjunction with any other subcommand.')
@click.pass_context
def main(ctx, suppress_confirmation):
    """
    vimeops - a simple downloader/uploader tool for Vimeo
    """
    ctx.ensure_object(dict)
    ctx.obj['AUTO'] = suppress_confirmation  # No input required from user: useful if you are scripting
    

    
@click.command(help='Rename the files in this way: root/title1/whatever.mp4 -> root/title1/title1.mp4')
@click.option('--path', nargs=1, type=str, default=INPUT_DIR, required=False, help='Source root folder. Its directory tree should be like: root/title1/whatever.mp4')
@click.option('--threshold', type=int, default=THRESHOLD, required=False, help='Threshold in megabytes beyond which the file will be ignored (default: 10)')
def rename(threshold, path):
    click.echo("Renaming...")

    # Handling exceptions
    if not path:
        click.echo(f"Path is null!")
        raise click.Abort()

    if not os.path.exists(path):
        click.echo(f"Path does not exist! Path provided: {path}")
        raise click.Abort()

    # Cycle in input directory
    for dir_name in os.listdir(path):
        full_dir_path = os.path.join(path, dir_name)

        # If it's really dealing with a dir
        if os.path.isdir(full_dir_path):
            counter = 1
            
            # Get mp4 files only
            mp4_files = [file for file in os.listdir(full_dir_path) if file.endswith('.mp4')]

            for file in mp4_files:
                old_full_name = os.path.join(full_dir_path, file)
                filesize = os.path.getsize(old_full_name)

                # If above the threshold, they are considered, else they will be skipped
                if filesize >= (int(threshold) * (10**6)):

                    if len(mp4_files) == 1:
                        new_full_name = os.path.join(full_dir_path, dir_name + ".mp4")
                    else:
                        # Multiple mp4: name these files like its parent folder, attaching "Part N" at the end
                        new_full_name = os.path.join(full_dir_path, dir_name + " - Parte " + str(counter) + ".mp4")
                        counter += 1

                    os.rename(old_full_name, new_full_name)
                    click.echo(old_full_name + " -> " + new_full_name)
                else:
                    click.echo(f"Skipping file {file}: too small! " + "{:.2f}".format(filesize/(10**6)) + f"MB < {threshold}MB\n")


@click.command(help='Upload your files to Vimeo. Destination path should be set from .env file or command line.')
@click.option('--path', nargs=1, default=INPUT_DIR, type=str, required=False, help="Absolute root path where videos are stored.")
@click.option('--client-id', nargs=1, default=CLIENT_ID, type=str, required=False, help="See Vimeo API Help for further information.")
@click.option('--client-secret', nargs=1, default=CLIENT_SECRET, type=str, required=False, help="See Vimeo API Help for further information.")
@click.option('--access-token', nargs=1, default=ACCESS_TOKEN, type=str, required=False, help="See Vimeo API Help for further information.")
@click.pass_context
def upload(ctx, client_id, client_secret, access_token, path=None):
    """
    Upload some videos, given an array of strings with some paths
    """

    # Handling exceptions
    if not path:
        click.echo(f"Path is null!")
        raise click.Abort()

    if not os.path.exists(path):
        click.echo(f"Path does not exist! Path provided: {path}")
        raise click.Abort()

    if not client_id or not client_secret or not access_token:
        click.echo(f"Vimeo credentials not provided. Missing client-id, client-secret or access-token.")
        raise click.Abort()

    # Handling log file
    with open('app/logs/upload.json', 'r') as infile:
        try:
            cached_data = json.load(infile)
        except json.JSONDecodeError:
            cached_data = {}

    # Filter mp4 files in dirs like videos/title1/whatever.mp4
    to_upload_pipeline = {os.path.join(root, file): 0 for root, _, files in os.walk(path) for file in files if file.endswith('.mp4')}
    
    # (if it's the first time)
    # Write the list of files to upload into the log file
    if not cached_data: 
        with open('app/logs/upload.json', 'w') as outfile:
            json.dump(to_upload_pipeline, outfile)

    # This dict contains merged keys from both what's supposed to be uploaded
    # and what has already been uploaded
    merged = dict(to_upload_pipeline, **cached_data)

    click.echo("The following files will be uploaded:\n" + "\n".join(merged))    
    
    # Useful if not scripting
    if not ctx.obj['AUTO']:
        input("Press [Enter] to continue or [CTRL+C] to exit...")
    
    # Connect to vimeo servers
    v = connect_to_vimeo(client_id, client_secret, access_token)

    # Upload each file to Vimeo
    for file_to_upload in list(merged.keys()):
        # If key in dict is 0, it means we have not uploaded the file
        if not merged[file_to_upload]:
            click.echo(f"Uploading {file_to_upload}...", nl=False)
            
            # If the transfer is successfull
            if(upload_single_file(file_to_upload, v)):
                merged[file_to_upload] = 1
                with open('app/logs/upload.json', 'w') as outfile:
                    json.dump(merged, outfile)
        else:
            click.echo(f"{file_to_upload} File has already been uploaded!")

@click.command(help='Download all your videos from your Vimeo account. Source path should be set from .env file or command line.')
@click.option('--path', nargs=1, default=DOWNLOAD_DIR, type=str, required=False, help="Absolute root path where videos will be stored.")
@click.option('--client-id', nargs=1, default=CLIENT_ID, type=str, required=False, help="See Vimeo API Help for further information.")
@click.option('--client-secret', nargs=1, default=CLIENT_SECRET, type=str, required=False, help="See Vimeo API Help for further information.")
@click.option('--access-token', nargs=1, default=ACCESS_TOKEN, type=str, required=False, help="See Vimeo API Help for further information.")
@click.argument('video-uri', nargs=1, type=str, required=False)
@click.pass_context
def download(ctx, client_id, client_secret, access_token, video_uri, path=None):
    """
    Download all your videos in your account.
    """

    # Handling exceptions
    if not path:
        click.echo(f"Path is null!")
        raise click.Abort()

    if not os.path.exists(path):
        click.echo(f"Path does not exist! Path provided: {path}")
        raise click.Abort()

    if not client_id or not client_secret or not access_token:
        click.echo(f"Vimeo credentials not provided. Missing client-id, client-secret or access-token.")
        raise click.Abort()

    # Connect and upload each file to Vimeo
    v = connect_to_vimeo(client_id, client_secret, access_token)

    # Download all videos
    try:
        videos = get_all_videos(v)

        click.echo("All your videos have been downloaded!")
    except Exception as e:
        click.echo(f"Error getting all videos! Reason: {e}")
        click.Abort()

    # Handling log file
    with open('app/logs/download.json', 'r') as infile:
        try:
            cached_data = json.load(infile)
        except json.JSONDecodeError:
            cached_data = {}

    # Build two arrays: one is for names, one is videos but with name as dict key
    to_download_pipeline = {v['name']: 0 for v in videos}
    videos = {v['name']: v for v in videos}

    # (if it's the first time)
    # Write the list of files to download into the log file
    if not cached_data:
        with open('app/logs/download.json', 'w') as outfile:
            json.dump(to_download_pipeline, outfile)

    # This dict contains merged keys from both what's supposed to be downloaded
    # and what has already been uploaded
    merged = dict(to_download_pipeline, **cached_data)

    click.echo("The following files will be downloaded:\n" + "\n".join(merged))    
    
    # Useful if not scripting
    if not ctx.obj['AUTO']:
        input("Press [Enter] to continue or [CTRL+C] to exit...")

    try:
        # Upload each file to Vimeo
        for file_to_download in list(merged.keys()):
            # If key in dict is 0, it means we have not downloaded the file
            if not merged[file_to_download]:
                click.echo(f"Downloading {file_to_download}...", nl=False)
                
                # If the transfer is successfull
                if(download_video(v, videos[file_to_download], path)):
                    merged[file_to_download] = 1
                    with open('app/logs/download.json', 'w') as outfile:
                        json.dump(merged, outfile)
            else:
                click.echo(f"{file_to_download} File has already been downloaded!")
        click.echo("All your videos have been downloaded!")
    except Exception as e:
        click.echo(f"An error has occurred: {e}")
        click.Abort()
    
main.add_command(rename)
main.add_command(upload)
main.add_command(download)

if __name__ == '__main__':
    main()

