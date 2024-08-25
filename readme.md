# renderer
Convention based script to render HTML from Markdown.

## Setup
Initialize the venv
`python3 -m venv .venv`

## Requirements
`pip install -r requirements.txt`

Also requires `pandoc` on the os. Run the following or use docker:

```
apt-get update
apt-get install -y pandoc 
apt-get clean
```

## Configuration
create a `config.ini` file with the following content

```
[paths]
content_dir = /home/user/Documents/my_markdown
output_dir = /home/ted/Documents/output
template_dir = templates
static_dir = static

[properties]
website_title=My Website
linkedin = mylinkedin
twitter = mytwitter
github = mygithub

```

## Running the venv
`source .venv/bin/activate`

## Running
`python3 generate.py`
