#!/usr/bin/env bash
set -e

NOTEBOOKS=(
  bmr-calculator
  steps-to-calories-burned
  steps-to-calories-burned-in-15-minutes
  steps-to-calories-burned-no-speed
  activity-time-to-met-calories-burned
)

for dir in "${NOTEBOOKS[@]}"; do
  echo "Building $dir..."
  ./node_modules/.bin/notebooks build "$dir/notebook.html" --root "$dir" --out dist
  ln -sfn dist/notebook.html "$dir/index.html"
  ln -sfn dist/assets "$dir/assets"
done

echo "Done."
