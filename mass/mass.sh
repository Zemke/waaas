#!/bin/bash

process() {
  local f=$1
  local out=$2
  local host=$3
  local id=$(echo $f | gsed -r 's/.*\/([0-9]+).*/\1/g')
  echo "Processing file $f which is file $id"
  local json=$(curl -X POST "$host" -F "replay=@${f}")
  local map=$(echo $json | gsed -r 's/.*"map": "(\/map\/[^"]+)".*/\1/g')
  echo "map is at $map"
  wget --wait 1 --limit-rate=150k -O $out/$id.png "${host}${map}"
  echo $json > $out/$id.json
}

if [[ $# -eq 0 ]]; then
  echo 'first param must be the WAaaS host (i.e. https://waaas.zemke.io)'
  echo 'second param must be a WAgame replay file or directory containing those'
  echo 'third param must be a dir for the output'
  exit 1
fi

host=$1
src=$2
out=$3

echo "outputting to $out"

if [[ -d $src ]]; then
  echo "processing WAgame files from dir $src"

  for f in $src/*; do
    [[ ! -r $f ]] && continue
    [[ $f != *.WAgame ]] && continue
    echo "file: $f"
    process "$f" "$out" "$host"
    sleep 1
  done
else
  if [[ -r $src ]]; then
    echo "processing WAgame file $src"
    process "$src" "$out" "$host"
  else
    echo "$src is neither directory nor readable file"
    exit 1
  fi
fi

echo done
exit 0

