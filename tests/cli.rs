use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use std::{fs, process};

use assert_cmd::Command;
use predicates::prelude::*;

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

fn parse_tsv(stdout: &str) -> Vec<(String, String)> {
    stdout
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| {
            let (hash, id) = line
                .split_once('\t')
                .unwrap_or_else(|| panic!("missing tab separator in line: {line}"));
            (hash.to_string(), id.to_string())
        })
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

#[test]
fn test_version_cli() {
    run_success(&["--version"]);
}

#[test]
fn test_single_record_cli() {
    let assert = run_success(&["MN908947.fasta"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 1);
    assert_eq!(rows[0].1, "MN908947.3");
    assert_eq!(rows[0].0, "33ba13564e0a63e3");
}

#[test]
fn test_multiple_records_cli() {
    let assert = run_success(&["MN908947-BA_2_86_1.fasta"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 3);
    assert_eq!(rows[0].1, "MN908947.3");
    assert_eq!(rows[1].1, "BA.2.86.1");
    assert_eq!(rows[2].1, "aggregate");
    assert_eq!(rows[0].0, "33ba13564e0a63e3");
    assert_eq!(rows[1].0, "9fef3b61d54d8902");
    assert_eq!(rows[2].0, "d3a94eb82357ece5");
}

#[test]
fn test_normalise() {
    let assert = run_success(&["normalise.fasta", "--normalise"]);
    let stdout = String::from_utf8(assert.get_output().stdout.clone()).unwrap();
    let rows = parse_tsv(&stdout);
    assert_eq!(rows.len(), 3);
    assert_eq!(rows[0].1, "t1");
    assert_eq!(rows[1].1, "t2");
    assert_eq!(rows[2].1, "aggregate");
    assert_eq!(rows[0].0, "3f4ec3194ceb8248");
    assert_eq!(rows[0].0, rows[1].0);
    assert_eq!(rows[2].0, "7e9d863299d70490");
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
fn test_exc_aggregate_single_record() {
    run_failure(&["MN908947.fasta", "--aggregate"])
        .stderr(predicate::str::contains("aggregate checksum unavailable"));
}

#[test]
fn test_logging_duplicate_sequences() {
    run_success(&["duplicate-sequences.fasta"])
        .stderr(predicate::str::contains("Found duplicate sequences"))
        .stderr(predicate::str::contains("1"))
        .stderr(predicate::str::contains("2"));
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
