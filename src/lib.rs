use std::io::Read;

use anyhow::{Result, anyhow, bail};
use paraseq::Record;
use paraseq::fastx::Reader;
use rapidhash::{HashMapExt, HashSetExt, RapidHashMap, RapidHashSet, v3::rapidhash_v3};

pub const DEFAULT_BITS: u8 = 64;

#[derive(Debug, Clone)]
pub struct SeqsumConfig {
    pub input: String,
    pub normalise: bool,
    pub strict: bool,
    pub bits: u8,
}

impl Default for SeqsumConfig {
    fn default() -> Self {
        Self {
            input: "-".to_string(),
            normalise: false,
            strict: false,
            bits: DEFAULT_BITS,
        }
    }
}

#[derive(Debug, Clone)]
pub struct SeqsumResult {
    pub aggregate: Option<u64>,
    pub duplicate_sequences: bool,
    pub duplicate_sequence_names: Vec<String>,
    pub checksum_collisions: bool,
    pub record_count: usize,
}

fn validate_bits(bits: u8) -> Result<()> {
    if !(4..=64).contains(&bits) || !bits.is_multiple_of(4) {
        bail!("bit depth must be a multiple of 4 between 4 and 64");
    }
    Ok(())
}

fn in_strict_nt_alphabet(base: u8) -> bool {
    matches!(
        base,
        b'A' | b'B'
            | b'C'
            | b'D'
            | b'G'
            | b'H'
            | b'K'
            | b'M'
            | b'N'
            | b'R'
            | b'S'
            | b'T'
            | b'V'
            | b'W'
            | b'Y'
            | b'-'
    )
}

fn normalise_sequence(seq: &[u8], normalise: bool, strict: bool, id: &str) -> Result<Vec<u8>> {
    let mut output = Vec::with_capacity(seq.len());

    for &base in seq {
        let upper = base.to_ascii_uppercase();
        if strict && !in_strict_nt_alphabet(upper) {
            bail!(
                "strict alphabet violation in record {id}: encountered '{}'",
                upper as char
            );
        }

        if normalise {
            let normalised = match upper {
                b'A' | b'C' | b'G' | b'T' | b'-' => upper,
                b'U' => b'T',
                _ => b'N',
            };
            output.push(normalised);
        } else {
            output.push(upper);
        }
    }

    Ok(output)
}

fn create_reader(input: &str) -> Result<Reader<Box<dyn Read + Send>>> {
    if input == "-" {
        let reader = Box::new(std::io::stdin()) as Box<dyn Read + Send>;
        Reader::new(reader).map_err(|e| anyhow!("failed to create stdin reader: {e}"))
    } else {
        Reader::from_path(input).map_err(|e| anyhow!("failed to open input {input}: {e}"))
    }
}

fn truncate_hash(hash: u64, bits: u8) -> u64 {
    if bits == 64 {
        hash
    } else {
        hash >> (64 - bits as u32)
    }
}

pub fn format_hash(hash: u64, bits: u8) -> String {
    let chars = (bits / 4) as usize;
    let full = format!("{hash:016x}");
    full[..chars].to_string()
}

pub fn sum_nt<F>(config: &SeqsumConfig, mut on_record: F) -> Result<SeqsumResult>
where
    F: FnMut(&str, u64) -> Result<()>,
{
    validate_bits(config.bits)?;

    let mut reader = create_reader(&config.input)?;
    reader
        .update_batch_size_in_bp(256 * 1024)
        .map_err(|e| anyhow!("failed to configure parser batch size: {e}"))?;

    let mut record_set = reader.new_record_set();
    let mut seen_names = RapidHashSet::new();
    let mut first_name_by_hash: RapidHashMap<u64, String> = RapidHashMap::new();
    let mut duplicate_sequence_names = RapidHashSet::new();
    let mut unique_truncated_hashes = RapidHashSet::new();
    let mut record_count = 0usize;
    let mut aggregate_hash = 0u64;

    while record_set
        .fill(&mut reader)
        .map_err(|e| anyhow!("failed while parsing records: {e}"))?
    {
        for record in record_set.iter() {
            let record = record.map_err(|e| anyhow!("failed while reading a record: {e}"))?;
            let id = String::from_utf8_lossy(record.id()).into_owned();
            if !seen_names.insert(id.clone()) {
                bail!("sequence contains duplicated identifiers: {id}");
            }

            let seq = normalise_sequence(&record.seq(), config.normalise, config.strict, &id)?;
            let hash = rapidhash_v3(&seq);

            record_count += 1;
            aggregate_hash = aggregate_hash.wrapping_add(hash);
            if let Some(first_id) = first_name_by_hash.get(&hash) {
                duplicate_sequence_names.insert(first_id.clone());
                duplicate_sequence_names.insert(id.clone());
            } else {
                first_name_by_hash.insert(hash, id.clone());
            }
            unique_truncated_hashes.insert(truncate_hash(hash, config.bits));

            on_record(&id, hash)?;
        }
    }

    let mut duplicate_sequence_names = duplicate_sequence_names.into_iter().collect::<Vec<_>>();
    duplicate_sequence_names.sort_unstable();

    let duplicate_sequences = !duplicate_sequence_names.is_empty();
    let checksum_collisions = unique_truncated_hashes.len() < first_name_by_hash.len();

    Ok(SeqsumResult {
        aggregate: (record_count > 0).then_some(aggregate_hash),
        duplicate_sequences,
        duplicate_sequence_names,
        checksum_collisions,
        record_count,
    })
}
