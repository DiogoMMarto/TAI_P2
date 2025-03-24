use std::collections::{HashMap, HashSet};
use std::fs;
use std::sync::Arc;

use clap::Parser;
use colored::*;
use indicatif::ProgressBar;
use rayon::prelude::*;
use chrono::Local;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    #[arg(short, long)]
    data: String,
    #[arg(short, long)]
    sequence: String,
    #[arg(short = 'k', long, default_value_t = 2)]
    context: usize,
    #[arg(short, long, default_value_t = 1.0)]
    alpha: f64,
    #[arg(short, long, default_value_t = 20)]
    top: usize,
    #[arg(short, long)]
    verbose: bool,
}

struct Model {
    ko: usize,
    alpha: f64,
    const_term: f64,
    table: Arc<HashMap<Vec<u8>, (HashMap<u8, usize>, usize)>>,
}

impl Model {
    fn new(text: &[u8], ko: usize, alpha: f64) -> Self {
        let alphabet: HashSet<u8> = text.iter().copied().collect();
        let alphabet_size = alphabet.len();
        let const_term = alpha * alphabet_size as f64;
        let table = Self::build_table(text, ko);
        Self {
            ko,
            alpha,
            const_term,
            table: Arc::new(table),
        }
    }

    fn build_table(text: &[u8], ko: usize) -> HashMap<Vec<u8>, (HashMap<u8, usize>, usize)> {
        let mut table = HashMap::new();
        for i in 0..text.len().saturating_sub(ko) {
            let context = &text[i..i + ko];
            let next_char = text[i + ko];
            
            let entry = table.entry(context.to_vec()).or_insert_with(|| (HashMap::new(), 0));
            entry.0.entry(next_char).and_modify(|c| *c += 1).or_insert(1);
            entry.1 += 1;
        }
        table
    }

    fn estimate_bits(&self, text: &[u8]) -> f64 {
        let mut sum = 0.0;
        let log2 = std::f64::consts::LN_2;
        
        for i in 0..text.len().saturating_sub(self.ko) {
            let context = &text[i..i + self.ko];
            let next_char = text[i + self.ko];
            
            let default = (HashMap::new(), 0);
            let (context_table, total) = self.table.get(context).unwrap_or(&default);
            let count = context_table.get(&next_char).copied().unwrap_or(0);
            
            let numerator = count as f64 + self.alpha;
            let denominator = *total as f64 + self.const_term;
            sum += (numerator / denominator).ln();
        }
        
        -sum / log2
    }

    fn nrc(&self, x: &[u8]) -> f64 {
        if x.len() <= self.ko {
            return 0.0;
        }
        let content = self.estimate_bits(x);
        let length_x = x.len() as f64;
        let alphabet_x: HashSet<u8> = x.iter().copied().collect();
        let alphabet_size = alphabet_x.len() as f64;
        let denominator = length_x - alphabet_size.log2();
        
        if denominator <= 0.0 {
            0.0
        } else {
            content / denominator
        }
    }
}

fn parse_database(text: &[u8]) -> Vec<(String, Vec<u8>)> {
    let mut ret = Vec::new();
    let mut sequences = text.split(|&b| b == b'@');
    sequences.next(); // Skip first empty segment
    
    for seq in sequences {
        let mut lines = seq.splitn(2, |&b| b == b'\n');
        let name_line = lines.next().unwrap_or_default();
        let name = String::from_utf8_lossy(name_line).to_string();
        let sequence_bytes = lines.next().unwrap_or_default().iter()
            .filter(|&&b| b != b'\n' && b != b'\r')
            .copied()
            .collect();
        ret.push((name, sequence_bytes));
    }
    ret
}

fn print_log(message: &str) {
    let now = Local::now();
    let timestamp = now.format("%H:%M:%S:%3f").to_string();
    println!("{} {}", timestamp.cyan(), message);
}

fn print_table(res: &[(String, f64)], top: usize) {
    const NRC_WIDTH: usize = 6;
    const IDENTIFIER_WIDTH: usize = 100;
    let horizontal = "═";
    let vertical = "║";
    let top_left = "╔";
    let top_right = "╗";
    let top_middle = "╦";
    let mid_left = "╠";
    let mid_horizontal = "╬";
    let mid_right = "╣";
    let bottom_left = "╚";
    let bottom_middle = "╩";
    let bottom_right = "╝";

    println!(
        "{}{}{}{}{}",
        top_left,
        horizontal.repeat(NRC_WIDTH + 2),
        top_middle,
        horizontal.repeat(IDENTIFIER_WIDTH + 2),
        top_right
    );

    println!(
        "{} {:^NRC_WIDTH$} {} {:^IDENTIFIER_WIDTH$} {}",
        vertical,
        "NRC".bold().yellow(),
        vertical,
        "Identifier".bold().yellow(),
        vertical
    );

    println!(
        "{}{}{}{}{}",
        mid_left,
        horizontal.repeat(NRC_WIDTH + 2),
        mid_horizontal,
        horizontal.repeat(IDENTIFIER_WIDTH + 2),
        mid_right
    );

    for (name, nrc) in res.iter().take(top) {
        let nrc_str = format!("{:.4}", nrc).cyan().to_string();
        let truncated_name = &name[..name.chars().take(IDENTIFIER_WIDTH).collect::<Vec<char>>().len()]; 
    
        println!(
            "{} {:<NRC_WIDTH$} {} {:<IDENTIFIER_WIDTH$} {}",
            vertical,
            nrc_str,
            vertical,
            truncated_name,
            vertical
        );
    }

    println!(
        "{}{}{}{}{}",
        bottom_left,
        horizontal.repeat(NRC_WIDTH + 2),
        bottom_middle,
        horizontal.repeat(IDENTIFIER_WIDTH + 2),
        bottom_right
    );
}

fn main() -> anyhow::Result<()> {
    let args = Args::parse();

    let database_bytes = fs::read(&args.data)?;
    let sequences = parse_database(&database_bytes);

    if args.verbose {
        print_log(&format!("[INFO] Database: loaded {} sequences", sequences.len()));
    }

    let sequence_bytes = fs::read(&args.sequence)?;
    let model = Model::new(&sequence_bytes, args.context, args.alpha);

    if args.verbose {
        print_log(&format!(
            "[INFO] Model: created with depth {} and alpha {:.2}",
            args.context, args.alpha
        ));
    }

    let pb = ProgressBar::new(sequences.len() as u64);
    let model_arc = Arc::new(model);

    let mut nrcs: Vec<(String, f64)> = sequences
        .par_iter()
        .map(|(name, seq)| {
            let nrc = model_arc.nrc(seq);
            pb.inc(1);
            (name.clone(), nrc)
        })
        .collect();

    pb.finish_and_clear();

    nrcs.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());

    if args.verbose {
        print_log(&format!(
            "[INFO] Similarity: calculated for {} sequences",
            nrcs.len()
        ));
    }

    print_table(&nrcs, args.top);

    Ok(())
}