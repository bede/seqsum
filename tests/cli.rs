use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use std::{fs, process};

use assert_cmd::Command;
use flate2::Compression;
use flate2::write::GzEncoder;
use predicates::prelude::*;
use tempfile::Builder;
use zstd::stream::write::Encoder as ZstdEncoder;

fn data_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/data")
}

fn run_success(args: &[&str]) -> assert_cmd::assert::Assert {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_seqsum"));
    cmd.args(args).current_dir(data_dir()).assert().success()
}

fn run_failure(args: &[&str]) -> assert_cmd::assert::Assert {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_seqsum"));
    cmd.args(args).current_dir(data_dir()).assert().failure()
}

fn parse_tsv(stdout: &str) -> Vec<Vec<String>> {
    stdout
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| line.split('\t').map(|s| s.to_string()).collect())
        .collect()
}

fn write_collision_fixture(path: &Path) {
    let mut data = String::new();
    for i in 0..17u8 {
        let seq = format!("{i:016b}")
            .chars()
            .map(|bit| if bit == '0' { 'A' } else { 'C' })
            .collect::<String>();
        data.push('>');
        data.push_str(&format!("r{i}\n"));
        data.push_str(&seq);
        data.push('\n');
    }
    fs::write(path, data).expect("failed to write temporary collision fixture");
}

fn fixture_fasta_bytes() -> &'static [u8] {
    b">r1\nACGTACGT\n>r2\nACGTACGA\n"
}

fn write_temp_gz() -> PathBuf {
    let file = Builder::new()
        .prefix("seqsum-gz-")
        .suffix(".fasta.gz")
        .tempfile()
        .expect("failed to create temporary .gz file");
    let path = file.path().to_path_buf();
    let mut encoder = GzEncoder::new(file, Compression::default());
    std::io::Write::write_all(&mut encoder, fixture_fasta_bytes())
        .expect("failed to write gzip fixture");
    let file = encoder.finish().expect("failed to finish gzip fixture");
    file.keep().expect("failed to persist temporary .gz file");
    path
}

fn write_temp_zst() -> PathBuf {
    let file = Builder::new()
        .prefix("seqsum-zst-")
        .suffix(".fasta.zst")
        .tempfile()
        .expect("failed to create temporary .zst file");
    let path = file.path().to_path_buf();
    let mut encoder = ZstdEncoder::new(file, 0).expect("failed to create zstd encoder");
    std::io::Write::write_all(&mut encoder, fixture_fasta_bytes())
        .expect("failed to write zstd fixture");
    let file = encoder.finish().expect("failed to finish zstd fixture");
    file.keep().expect("failed to persist temporary .zst file");
    path
}

#[test]
fn test_version_cli() {
    run_success(&["--version"]);
}

#[test]
fn test_default_single_record() {
    let assert = run_success(&["MN908947.fasta"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 1);
    assert_eq!(rows[0], vec!["33ba13564e0a63e3", "MN908947.fasta"]);
}

#[test]
fn test_default_multiple_records() {
    let assert = run_success(&["MN908947-BA_2_86_1.fasta"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 1);
    assert_eq!(
        rows[0],
        vec!["d3a94eb82357ece5", "MN908947-BA_2_86_1.fasta"]
    );
}

#[test]
fn test_individual_single_record() {
    let assert = run_success(&["-i", "MN908947.fasta"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 1);
    assert_eq!(rows[0], vec!["33ba13564e0a63e3", "MN908947.3"]);
}

#[test]
fn test_individual_multiple_records() {
    let assert = run_success(&["-i", "MN908947-BA_2_86_1.fasta"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 2);
    assert_eq!(rows[0], vec!["33ba13564e0a63e3", "MN908947.3"]);
    assert_eq!(rows[1], vec!["9fef3b61d54d8902", "BA.2.86.1"]);
}

#[test]
fn test_all_mode() {
    let assert = run_success(&["-a", "MN908947-BA_2_86_1.fasta"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 3);
    assert_eq!(
        rows[0],
        vec!["33ba13564e0a63e3", "MN908947.3", "MN908947-BA_2_86_1.fasta"]
    );
    assert_eq!(
        rows[1],
        vec!["9fef3b61d54d8902", "BA.2.86.1", "MN908947-BA_2_86_1.fasta"]
    );
    assert_eq!(
        rows[2],
        vec!["d3a94eb82357ece5", "sum", "MN908947-BA_2_86_1.fasta"]
    );
}

#[test]
fn test_multi_file() {
    let assert = run_success(&["MN908947.fasta", "MN908947-BA_2_86_1.fasta"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 2);
    assert_eq!(rows[0], vec!["33ba13564e0a63e3", "MN908947.fasta"]);
    assert_eq!(
        rows[1],
        vec!["d3a94eb82357ece5", "MN908947-BA_2_86_1.fasta"]
    );
}

#[test]
fn test_multi_file_all_mode() {
    let assert = run_success(&["-a", "MN908947.fasta", "MN908947-BA_2_86_1.fasta"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 5);
    assert_eq!(
        rows[0],
        vec!["33ba13564e0a63e3", "MN908947.3", "MN908947.fasta"]
    );
    assert_eq!(rows[1], vec!["33ba13564e0a63e3", "sum", "MN908947.fasta"]);
    assert_eq!(
        rows[2],
        vec!["33ba13564e0a63e3", "MN908947.3", "MN908947-BA_2_86_1.fasta"]
    );
    assert_eq!(
        rows[3],
        vec!["9fef3b61d54d8902", "BA.2.86.1", "MN908947-BA_2_86_1.fasta"]
    );
    assert_eq!(
        rows[4],
        vec!["d3a94eb82357ece5", "sum", "MN908947-BA_2_86_1.fasta"]
    );
}

#[test]
fn test_stdin_default() {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_seqsum"));
    let assert = cmd
        .pipe_stdin(data_dir().join("MN908947.fasta"))
        .unwrap()
        .assert()
        .success();
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 1);
    assert_eq!(rows[0], vec!["33ba13564e0a63e3", "-"]);
}

#[test]
fn test_individual_all_conflict() {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_seqsum"));
    cmd.args(["-i", "-a", "MN908947.fasta"])
        .current_dir(data_dir())
        .assert()
        .failure();
}

#[test]
fn test_normalise() {
    let assert = run_success(&["-i", "normalise.fasta", "--normalise"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 2);
    assert_eq!(rows[0], vec!["3f4ec3194ceb8248", "t1"]);
    assert_eq!(rows[0][0], rows[1][0]);
}

#[test]
fn test_strict_pass() {
    run_success(&["strict-pass.fasta", "--strict"]);
}

#[test]
fn test_exc_strict_fail() {
    run_failure(&["strict-fail.fasta", "--strict"])
        .stderr(predicate::str::contains("strict alphabet violation"));
}

#[test]
fn test_exc_invalid_path() {
    run_failure(&["non-existent.fasta"]).stderr(predicate::str::contains("failed to open input"));
}

#[test]
fn test_exc_duplicate_names() {
    run_failure(&["duplicate-names.fasta", "--strict"])
        .stderr(predicate::str::contains("duplicated identifiers"));
}

#[test]
fn test_exc_invalid_bit_depth() {
    run_failure(&["MN908947.fasta", "--bits", "9"]).stderr(predicate::str::contains(
        "bit depth must be a multiple of 4 between 4 and 64",
    ));
}

#[test]
fn test_logging_duplicate_sequences() {
    run_success(&["duplicate-sequences.fasta"])
        .stderr(predicate::str::contains("Found duplicate sequences"));
}

#[test]
fn test_logging_duplicate_sequences_verbose() {
    run_success(&["duplicate-sequences.fasta", "--verbose"])
        .stderr(predicate::str::contains("Found duplicate sequences"))
        .stderr(predicate::str::contains("1"))
        .stderr(predicate::str::contains("2"));
}

#[test]
fn test_quiet_suppresses_stderr() {
    run_success(&["duplicate-sequences.fasta", "--quiet"]).stderr(predicate::str::is_empty());
}

#[test]
fn test_logging_collisions() {
    let unique = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("clock should be monotonic enough")
        .as_nanos();
    let path =
        std::env::temp_dir().join(format!("seqsum-collision-{}-{unique}.fasta", process::id()));
    write_collision_fixture(&path);
    let path_string = path.to_string_lossy().to_string();

    run_success(&[&path_string, "--bits", "4"])
        .stderr(predicate::str::contains("Found checksum collisions"));

    let _ = fs::remove_file(path);
}

#[test]
fn test_gz() {
    let path = write_temp_gz();
    let path_string = path.to_string_lossy().to_string();

    let assert = run_success(&[&path_string]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 1);
    assert_eq!(rows[0][1], path_string);

    let _ = fs::remove_file(path);
}

#[test]
fn test_zst() {
    let path = write_temp_zst();
    let path_string = path.to_string_lossy().to_string();

    let assert = run_success(&[&path_string]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 1);
    assert_eq!(rows[0][1], path_string);

    let _ = fs::remove_file(path);
}
