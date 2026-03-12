use power_scanner::{parse_gpx_string, scan_to_json};
use std::env;
use std::fs;

fn main() {
    let args: Vec<String> = env::args().collect();
    let gpx_path = args.get(1).map(|s| s.as_str()).unwrap_or("sample-ride.gpx");
    let output_path = args.get(2).map(|s| s.as_str()).unwrap_or("power_data.json");
    let rest_secs: usize = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(0);

    let xml = fs::read_to_string(gpx_path).expect("Failed to read GPX file");
    let samples = parse_gpx_string(&xml);
    if samples.is_empty() {
        eprintln!("No power data found!");
        std::process::exit(1);
    }

    eprintln!("Parsed {} seconds of data", samples.len());
    eprintln!("Rest mode: {}", if rest_secs == 0 { "equal".to_string() } else { format!("{}s fixed", rest_secs) });

    let json = scan_to_json(&samples, rest_secs);
    fs::write(output_path, &json).unwrap();
    eprintln!("Written to {}", output_path);
}
