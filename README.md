# Moved to a new site

This repo is no longer maintained.

The new repo is located here: https://github.com/tgig/GBlog

---

# Gig-a-blog

The content for this blog and miki are automatically refreshed when a commit is pushed to [the Miki repo here](https://github.com/tgig/Miki).

When the push happens, a Github Action is kicked off to pull the new data out of that repo and put it into the `/content` folder of this repo.

## Run

`python blog.py`

## Freeze

`python blog.py build`

## Deploy to prod

`git push`
