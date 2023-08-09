# Vimeops

a simple Python utility that manage your videos, allowing you to download and upload to Vimeo. 

## Features
This utility supports the following operations:
- [X] **Files renaming** contained in the subfolders -related to the parent folder-, and directly uploads them on your Vimeo account. See below for further information.
- [X] **Upload** files given a folder tree. See below.
- [X] Installable command: you can install into your environment and use it
- [X] **Cache** in case of downtime or already uploaded files
- [X] **Download** the entire library in the account

If needed a **filesize threshold**, in megabytes, could be set, in a way that if a file is lower than this threshold, **it will be ignored**. (default: *10mb*)

e.g. this directory tree:
```
DirectoryWithALongName/
├── 2019-07-30 15.13.50 Meeting1
│   ├── audio_only.m4a
│   ├── playback.m3u
│   ├── whatever_0.mp4
│   └── whatever_1.mp4
├── 20200911-Meeting2
│   └── whatever_0.mp4
└── 20211116-Meeting3
    └── QuickMeeting 2021-11-16-134337.mp4
```

will become like this:
```
DirectoryWithALongName/
├── 2019-07-30 15.13.50 Meeting1
│   ├── audio_only.m4a
│   ├── playback.m3u
│   ├── 2019-07-30 15.13.50 Meeting1 - Part One.mp4
│   └── 2019-07-30 15.13.50 Meeting1 - Part Two.mp4
├── 20200911-Meeting2
│   └── 20200911-Meeting2.mp4
└── 20211116-Meeting3
    └── 20211116-Meeting3.mp4
```



## Requirements
- Directory tree named like you prefer (see example for further information)

- Python3.9+

- a Vimeo account, with `CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN` and Upload Access permission enabled. 

    - [Create an app here](https://developer.vimeo.com/apps) with these scopes: `private create edit upload video_files public`.

    - [Vimeo Developer Docs](https://developer.vimeo.com) for more information


- Pipenv (optional)

## Setup
1. Setup a virtual environment and install `requirements.txt` with Pip, or if using Pipenv
```
pipenv shell
pipenv install
```

2. Create and fill the `.env` file in `app` directory. See `.env.sample` for further information. Optionally, these params could be **overrided by command line**. See [usage and examples](#usage-and-examples) section.

3. Open a new terminal in the vimeops foledr and install `vimeops` by giving `pip install --editable .`. Remember to stay in the pipenv environment.

## Usage and examples
1. Rename files with default config (.env file)
```
vimeops rename
```

2. Rename files with path provided by command line
```
vimeops rename --path=/home/user/Videos/VideosToRename/
```

3. Upload mp4 in the dirtree, providing sensitive data by command line (not reccomended). All of them must be provided.
```
vimeops upload --client-id <your-client-id> --client-secret <your-client-secret> --access-token <your-access-token> 
```

4. Download all your uploaded videos.
```
vimeops --suppress-confirmation download
```

5. Doing anything without confirmation or summary. Useful for scripts.
```
vimeops --suppress-confirmation <whatever-command>
```

6. Rename and upload the files
```
vimeops --suppress-confirmation rename && vimeops --suppress-confirmation upload
```

## Progress bar
This manual patch enables a progress bar, even if we need to manually patch the library:
https://github.com/tus/tus-py-client/pull/41/files

It is not currently enabled.
