#!/bin/bash
# update.sh - generates a new rendered html page, moves it to the directory
# being served, and attempts to inform if this might have failed.

# Example use in dev environment:
# ./update.sh rendered.html ./www/ ~/projects/veg.fi/
# Used in production by cron, as per something like this:
# 5 0 * * * ~/update.sh rendered.html /data/www/ ~/ >> cron.log

file="$1"
out_path="$2"
program_root_path="$3"

eval cd "$program_root_path" || {
    date | tr -d '\n'
    echo " --- UPDATE FAILED: Failed to cd to program directory."
    exit 1
}

if [ -f "$file" ]; then
    date | tr -d '\n'
    echo " --- Rendered template already exists here, even though it shouldn't. Removing..."
    rm "$file"
fi

if [ -f "$file" ]; then
    date | tr -d '\n'
    echo " --- UPDATE FAILED: Couldn't remove previously rendered template."
    exit 1
fi

PYTHONPATH="." "$HOME"/env/bin/python -m vegfi.veg

if [ ! -f "$file" ]; then
    date | tr -d '\n'
    echo " --- UPDATE FAILED: Could not create file."
    exit 1
fi

mv "$file" "$out_path""$file"

if [ -f "$file" ]; then
    date | tr -d '\n'
    echo " --- UPDATE FAILED: Could not move rendered template to www dir (unless you're creating straight to www dir)."
    exit 1
fi

date | tr -d '\n'
echo " --- Success!"

exit 0
