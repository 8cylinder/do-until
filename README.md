
# do-until

Run a command until a specific time.

This is the same functionality as `timeout`, but pretty.  It shows a
progressbar that counts down until the TIME.


## Install

Clone the repo and use [uv](https://docs.astral.sh/uv/) to install it.

``` bash
git clone <this-repo>
cd do-until
uv build
uv install dist/do_until*.whl
```

## Usage

``` bash
do-until --help
do-until 10s ping google.com
do-until 'in 1h' -- ping -h
```
