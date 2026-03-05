#!/usr/bin/env bash
# Usage: ./download.sh   (re-downloads all)
#        ./download.sh bmr-calculator  (re-downloads one)
set -e

download_notebook() {
  local dir=$1
  local url=$2
  echo "Downloading $dir..."
  ./node_modules/.bin/notebooks download "$url" > "$dir/notebook.html"
}

case "${1:-all}" in
  bmr-calculator)
    download_notebook bmr-calculator "https://observablehq.com/@andyreagan/bmr-calculator" ;;
  steps-to-calories-burned)
    download_notebook steps-to-calories-burned "https://observablehq.com/@andyreagan/steps-to-calories-burned@136" ;;
  steps-to-calories-burned-in-15-minutes)
    download_notebook steps-to-calories-burned-in-15-minutes "https://observablehq.com/@andyreagan/steps-to-calories-burned-in-15-minutes@59" ;;
  steps-to-calories-burned-no-speed)
    download_notebook steps-to-calories-burned-no-speed "https://observablehq.com/@andyreagan/steps-to-calories-burned-no-speed@77" ;;
  activity-time-to-met-calories-burned)
    download_notebook activity-time-to-met-calories-burned "https://observablehq.com/@andyreagan/activity-time-to-met-calories-burned@134" ;;
  all)
    download_notebook bmr-calculator "https://observablehq.com/@andyreagan/bmr-calculator"
    download_notebook steps-to-calories-burned "https://observablehq.com/@andyreagan/steps-to-calories-burned@136"
    download_notebook steps-to-calories-burned-in-15-minutes "https://observablehq.com/@andyreagan/steps-to-calories-burned-in-15-minutes@59"
    download_notebook steps-to-calories-burned-no-speed "https://observablehq.com/@andyreagan/steps-to-calories-burned-no-speed@77"
    download_notebook activity-time-to-met-calories-burned "https://observablehq.com/@andyreagan/activity-time-to-met-calories-burned@134"
    ;;
  *)
    echo "Unknown notebook: $1"; exit 1 ;;
esac

echo "Done. Run 'npm run build' to rebuild."
