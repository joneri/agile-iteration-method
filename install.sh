#!/bin/sh
set -eu

AIM_REPO="${AIM_REPO:-joneri/agile-iteration-method}"
AIM_REF="${AIM_REF:-${AIM_VERSION:-main}}"
AIM_TARGET="${AIM_TARGET:-$(pwd)}"

die() {
  printf '%s\n' "AIM install: $*" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

has_arg() {
  needle="$1"
  shift
  for value in "$@"; do
    case "$value" in
      "$needle"|"$needle"=*) return 0 ;;
    esac
  done
  return 1
}

need curl
need tar
need python3
need mktemp

case "$AIM_REF" in
  "")
    die "AIM_REF must not be empty"
    ;;
esac

archive_url="https://github.com/${AIM_REPO}/archive/${AIM_REF}.tar.gz"
tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/aim-install.XXXXXX")"

cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT INT TERM

printf '%s\n' "AIM install: fetching ${AIM_REPO} ${AIM_REF}"
curl -fsSL "$archive_url" -o "$tmp_dir/aim.tar.gz"
mkdir "$tmp_dir/src"
tar -xzf "$tmp_dir/aim.tar.gz" -C "$tmp_dir/src" --strip-components 1

set -- "$@"
if ! has_arg "--target" "$@"; then
  set -- --target "$AIM_TARGET" "$@"
fi
if ! has_arg "--source" "$@"; then
  set -- --source "$tmp_dir/src" "$@"
fi

if [ -r /dev/tty ] && [ -w /dev/tty ]; then
  python3 "$tmp_dir/src/scripts/aim_install.py" "$@" < /dev/tty
else
  python3 "$tmp_dir/src/scripts/aim_install.py" "$@"
fi
