use std::io::{BufWriter, Write};

use anyhow::{Result, anyhow};
use clap::Parser;

use seqsum::{DEFAULT_BITS, SeqsumConfig, format_hash, sum_nt};

#[derive(Debug, Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    /// Path to FASTA/FASTQ input, or - for stdin.
    #[arg(default_value = "-")]
    input: String,

    /// Replace U with T, and non-ACGT- characters with N before hashing.
    #[arg(short = 'n', long)]
    normalise: bool,

    /// Require IUPAC ambiguous DNA alphabet ABCDGHKMNRSTVWY-.
    #[arg(short = 's', long)]
    strict: bool,

    /// Displayed hash length in bits (4..64, multiple of 4).
    #[arg(short = 'b', long, default_value_t = DEFAULT_BITS)]
    bits: u8,

    /// Output only per-record checksums.
    #[arg(short = 'i', long)]
    individual: bool,

    /// Output only the aggregate checksum.
    #[arg(short = 'a', long)]
    aggregate: bool,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let config = SeqsumConfig {
        input: cli.input.clone(),
        normalise: cli.normalise,
        strict: cli.strict,
        bits: cli.bits,
    };

    let show_individual = cli.individual || !cli.aggregate;

    let stdout = std::io::stdout();
    let mut out = BufWriter::new(stdout.lock());

    let result = sum_nt(&config, |id, hash| {
        if show_individual {
            writeln!(out, "{}\t{id}", format_hash(hash, cli.bits))?;
        }
        Ok(())
    })?;

    if result.duplicate_sequences {
        eprintln!(
            "INFO: Found duplicate sequences: {}",
            result.duplicate_sequence_names.join(", ")
        );
    }
    if result.checksum_collisions {
        eprintln!("WARNING: Found checksum collisions, consider increasing --bits");
    }

    let show_aggregate = if cli.aggregate {
        true
    } else if cli.individual {
        false
    } else {
        result.record_count > 1
    };

    if show_aggregate {
        let aggregate = result
            .aggregate
            .ok_or_else(|| anyhow!("aggregate checksum unavailable"))?;
        writeln!(out, "{}\taggregate", format_hash(aggregate, cli.bits))?;
    }

    out.flush()?;
    Ok(())
}
