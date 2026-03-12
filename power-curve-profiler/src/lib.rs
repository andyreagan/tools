use quick_xml::events::Event;
use quick_xml::Reader;
use wasm_bindgen::prelude::*;

// ─── GPX parsing ─────────────────────────────────────────────────────────

/// Parse GPX XML string and extract 1-second power samples.
pub fn parse_gpx_string(xml: &str) -> Vec<f64> {
    let mut reader = Reader::from_str(xml);
    let mut buf = Vec::new();

    struct TrkPt {
        time_secs: u64,
        power: f64,
    }

    let mut points: Vec<TrkPt> = Vec::new();
    let mut in_trkpt = false;
    let mut in_time = false;
    let mut in_power = false;
    let mut depth = 0u32;
    let mut current_time: Option<u64> = None;
    let mut current_power: Option<f64> = None;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(ref e)) => {
                let name = e.local_name();
                if name.as_ref() == b"trkpt" {
                    in_trkpt = true;
                    depth = 0;
                    current_time = None;
                    current_power = None;
                }
                if in_trkpt {
                    depth += 1;
                    if name.as_ref() == b"time" && depth <= 3 {
                        in_time = true;
                    }
                    if name.as_ref() == b"power" {
                        in_power = true;
                    }
                }
            }
            Ok(Event::End(ref e)) => {
                let name = e.local_name();
                if in_trkpt {
                    if name.as_ref() == b"time" {
                        in_time = false;
                    }
                    if name.as_ref() == b"power" {
                        in_power = false;
                    }
                    depth = depth.saturating_sub(1);
                }
                if name.as_ref() == b"trkpt" {
                    if let (Some(t), Some(p)) = (current_time, current_power) {
                        points.push(TrkPt {
                            time_secs: t,
                            power: p,
                        });
                    }
                    in_trkpt = false;
                }
            }
            Ok(Event::Text(ref e)) => {
                let text = e.unescape().unwrap_or_default();
                let text = text.trim();
                if in_time && in_trkpt {
                    if let Some(secs) = parse_iso8601(text) {
                        current_time = Some(secs);
                    }
                    in_time = false;
                }
                if in_power && in_trkpt {
                    if let Ok(p) = text.parse::<f64>() {
                        current_power = Some(p);
                    }
                    in_power = false;
                }
            }
            Ok(Event::Eof) => break,
            Err(_) => break,
            _ => {}
        }
        buf.clear();
    }

    if points.is_empty() {
        return Vec::new();
    }

    points.sort_by_key(|p| p.time_secs);

    let t0 = points[0].time_secs;
    let t_end = points.last().unwrap().time_secs;
    let total_seconds = (t_end - t0) as usize;

    let mut samples = vec![0.0f64; total_seconds + 1];
    for pt in &points {
        let idx = (pt.time_secs - t0) as usize;
        if idx < samples.len() {
            samples[idx] = pt.power;
        }
    }

    samples
}

fn parse_iso8601(s: &str) -> Option<u64> {
    let s = s.trim_end_matches('Z');
    let parts: Vec<&str> = s.split('T').collect();
    if parts.len() != 2 {
        return None;
    }
    let date_parts: Vec<u32> = parts[0].split('-').filter_map(|x| x.parse().ok()).collect();
    let time_parts: Vec<&str> = parts[1].split(':').collect();
    if date_parts.len() != 3 || time_parts.len() != 3 {
        return None;
    }
    let hour: u32 = time_parts[0].parse().ok()?;
    let min: u32 = time_parts[1].parse().ok()?;
    let sec: u32 = time_parts[2].split('.').next()?.parse().ok()?;

    let year = date_parts[0];
    let month = date_parts[1];
    let day = date_parts[2];

    let mut days: u64 = 0;
    for y in 1970..year {
        days += if is_leap(y) { 366 } else { 365 };
    }
    let month_days = [
        31,
        28 + if is_leap(year) { 1 } else { 0 },
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
    ];
    for m in 0..(month as usize - 1) {
        days += month_days[m] as u64;
    }
    days += (day - 1) as u64;

    Some(days * 86400 + hour as u64 * 3600 + min as u64 * 60 + sec as u64)
}

fn is_leap(y: u32) -> bool {
    (y % 4 == 0 && y % 100 != 0) || y % 400 == 0
}

// ─── Power scanning ──────────────────────────────────────────────────────

/// Compute prefix sums for O(1) range sum queries
pub fn prefix_sums(data: &[f64]) -> Vec<f64> {
    let mut ps = vec![0.0; data.len() + 1];
    for i in 0..data.len() {
        ps[i + 1] = ps[i] + data[i];
    }
    ps
}

/// For a given duration, repeat count, and rest duration, find the maximum
/// average "on" power across all possible starting positions.
///
/// Pattern for `repeats` efforts of `dur` seconds with `rest` seconds between:
///   Total window = repeats * dur + (repeats - 1) * rest
///   On-block k starts at k * (dur + rest) and covers dur seconds.
///
/// Uses sliding window with O(n * repeats) per call.
pub fn best_repeated_power(ps: &[f64], n: usize, dur: usize, repeats: usize, rest: usize) -> f64 {
    if dur == 0 || repeats == 0 {
        return 0.0;
    }
    let window = repeats * dur + (repeats - 1) * rest;
    if window > n {
        return f64::NAN;
    }

    let total_on = repeats * dur;
    let stride = dur + rest; // distance between starts of consecutive on-blocks

    // Initial sum at start=0
    let mut current_sum = 0.0;
    for k in 0..repeats {
        let block_start = k * stride;
        let block_end = block_start + dur;
        current_sum += ps[block_end] - ps[block_start];
    }
    let mut best_sum = current_sum;

    // Slide by 1 each step
    let max_start = n - window;
    for start in 1..=max_start {
        for k in 0..repeats {
            let old_idx = (start - 1) + k * stride;
            let new_idx = start + k * stride + dur - 1;
            current_sum -= ps[old_idx + 1] - ps[old_idx];
            current_sum += ps[new_idx + 1] - ps[new_idx];
        }
        if current_sum > best_sum {
            best_sum = current_sum;
        }
    }

    best_sum / total_on as f64
}

// ─── Duration helpers ────────────────────────────────────────────────────

const DURATIONS: &[usize] = &[
    1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 300, 360, 420, 480, 600, 720, 900,
    1200, 1500, 1800, 2400, 3600,
];

const MAX_REPEATS: usize = 10;

fn duration_label(d: usize) -> String {
    if d < 60 {
        format!("{}s", d)
    } else if d < 3600 {
        if d % 60 == 0 {
            format!("{}m", d / 60)
        } else {
            format!("{}m{}s", d / 60, d % 60)
        }
    } else {
        format!("{}h", d / 3600)
    }
}

/// Run the full scan and return JSON string.
/// `rest_mode`: 0 = equal rest (rest = effort duration), >0 = fixed rest in seconds.
pub fn scan_to_json(samples: &[f64], rest_mode: usize) -> String {
    let n = samples.len();
    let ps = prefix_sums(samples);

    let durations: Vec<usize> = DURATIONS.iter().copied().filter(|&d| d <= n).collect();

    // Build all (duration, repeat) pairs, filtering by what fits in the data
    let pairs: Vec<(usize, usize)> = durations
        .iter()
        .flat_map(|&d| {
            let rest = if rest_mode == 0 { d } else { rest_mode };
            (1..=MAX_REPEATS)
                .filter(move |&r| {
                    let window = r * d + (r - 1) * rest;
                    window <= n
                })
                .map(move |r| (d, r))
        })
        .collect();

    // Sequential computation (WASM is single-threaded)
    let results: Vec<(usize, usize, f64)> = pairs
        .iter()
        .map(|&(dur, rep)| {
            let rest = if rest_mode == 0 { dur } else { rest_mode };
            let power = best_repeated_power(&ps, n, dur, rep, rest);
            (dur, rep, power)
        })
        .collect();

    // Assemble grid
    let mut data_grid: Vec<Vec<serde_json::Value>> = Vec::new();
    for r in 1..=MAX_REPEATS {
        let mut row = Vec::new();
        for &d in &durations {
            let val = results
                .iter()
                .find(|&&(dd, rr, _)| dd == d && rr == r)
                .map(|&(_, _, p)| {
                    if p.is_nan() {
                        serde_json::Value::Null
                    } else {
                        serde_json::json!(p)
                    }
                })
                .unwrap_or(serde_json::Value::Null);
            row.push(val);
        }
        data_grid.push(row);
    }

    let duration_labels: Vec<String> = durations.iter().map(|&d| duration_label(d)).collect();

    let rest_label = if rest_mode == 0 {
        "equal".to_string()
    } else {
        format!("{}s", rest_mode)
    };

    let json = serde_json::json!({
        "durations_sec": durations,
        "duration_labels": duration_labels,
        "max_repeats": MAX_REPEATS,
        "total_seconds": n,
        "rest_mode": rest_label,
        "data": data_grid,
    });

    serde_json::to_string(&json).unwrap()
}

// ─── WASM entry point ────────────────────────────────────────────────────

/// Called from JavaScript with the GPX file contents as a string.
/// `rest_secs`: 0 = equal rest (rest duration = effort duration), >0 = fixed rest in seconds.
/// Returns a JSON string with the power data grid.
#[wasm_bindgen]
pub fn process_gpx(gpx_contents: &str, rest_secs: usize) -> String {
    let samples = parse_gpx_string(gpx_contents);
    if samples.is_empty() {
        return r#"{"error":"No power data found in GPX file"}"#.to_string();
    }
    scan_to_json(&samples, rest_secs)
}
