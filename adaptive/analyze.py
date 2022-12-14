#!/usr/bin/env python
import random
import sys

import pandas as pd



from argparse import (ArgumentParser, ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter)
import subprocess as sp
import os
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict
from adaptive.version import __version__
from adaptive import init_console_logger, run_command
from adaptive.constants import dependencies
import psutil
import shutil
import json
from subprocess import Popen, PIPE


def parse_args():
    class CustomFormatter(ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter):
        pass

    parser = ArgumentParser(
        description="Adaptive: Evaluate adaptive sampling runs v. {}".format(__version__),
        formatter_class=CustomFormatter)

    parser._optionals.title = "Arguments"
    parser.add_argument("-t", "--test_data", nargs="+", required=True,
                        help="[REQUIRED] Path to test fastq files to process.")
    parser.add_argument("-c", "--control_data", nargs="+",
                        help="[OPTIONAL] Path to CONTROL fastq file to process.")
    parser.add_argument("-d", "--db", required=True,
                        help="[REQUIRED] Path to reference fasta")
    parser.add_argument("-r", "--sample_report", nargs="+",
                        help="[CONDIOTNALLY REQUIRED] Path to adaptive sampling report generated by sequencer. Used to generate a classification-based report.")
    parser.add_argument('--sample_id', type=str, required=False, help='Sample name for experiment')

    parser.add_argument('--exclude', required=False, help='DB is to be used for exclusion')
    parser.add_argument('--outdir', type=str, required=True, help='Output Directory for results')
    parser.add_argument('--prefix', type=str, required=False, help='Prefix for output files', default='adaptive')

    parser.add_argument("--classify", action='store_true',
                        help="[OPTIONAL] Setting the option as True will generate a calssifcation based report. adaptive sampling report required for the classification based report.")

    parser.add_argument('--dedup', required=False, help='Deduplicate identical reads', action='store_true')
    parser.add_argument('--min_length', type=int, required=False, help='Min read length', default=0)
    parser.add_argument('--max_length', type=int, required=False, help='Max read length', default=0)
    parser.add_argument('--num_threads', type=int, required=False, help='Number of threads to use', default=1)
    parser.add_argument('--keep_tmp', required=False, help='Keep interim files', action='store_true')
    parser.add_argument('--debug', required=False, help='Show debug information', action='store_true')
    parser.add_argument('-v', '--version', action='version', version="%(prog)s " + __version__)

    return parser.parse_args()

def is_non_zero_file(fpath):
    '''
    Accepts path of file and tests if file exists and is not empty
    :param fpath:[string]
    :return: [boolean] True if file exists and not empty
    '''
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0

def run_fastp(read_set,out_dir,out_prefix,min_read_len=0,max_read_len=0,trim_front_bp=0,trim_tail_bp=0,report_only=True,dedup=False,n_threads=1):
    '''

    :param read_set:
    :param out_dir:
    :param out_prefix:
    :param min_read_len:
    :param max_read_len:
    :param trim_front_bp:
    :param trim_tail_bp:
    :param report_only:
    :param dedup:
    :param n_threads:
    :return:
    '''
    json = os.path.join(out_dir,"{}.json".format(out_prefix))
    html = os.path.join(out_dir, "{}.html".format(out_prefix))
    out1 = os.path.join(out_dir, "{}.fastp.fastq".format(out_prefix))

    cmd_args = {'-j ':json, '-h ':html, '-w ':n_threads}
    cmd_args['-i '] = read_set
    cmd_args['-f '] = trim_front_bp
    cmd_args['-t '] = trim_tail_bp
    cmd_args['-l '] = min_read_len
    cmd_args['--length_limit '] = max_read_len
    if dedup:
        cmd_args['-D '] = ''
    if not report_only:
        cmd_args['-o '] = out1

    cmd = "fastp {}".format((" ".join(f'{k}{v}' for k,v in cmd_args.items())))
    (stdout,stderr) = run_command(cmd)
    return process_json(json)

def process_json(json_path):
    '''

    :param json_path:
    :return:
    '''

    with open(json_path) as json_file:
        return json.load(json_file)

    return {}

def run_nanoplot(fastq,outdir,prefix,read_type='1D',num_threads=1):
    '''

    :param fastq:
    :param outdir:
    :param prefix:
    :param read_type:
    :param num_threads:
    :return:
    '''
    command = ['minimap','-t',num_threads,"--no_static",
               '--fastq',fastq,"--outdir",outdir,"--tsv_stats",
               "--prefix",prefix,'--read_type',read_type

    ]
    (stdout,stderr) = run_command(" ".join([str(x) for x in command]))
    return (stdout,stderr)



def convert_bam_to_fastq(bam_file,out_file,num_threads):
    '''

    :param bam_file:
    :param out_file:
    :param num_threads:
    :return:
    '''
    command = [
        'samtools', 'fastq' '-@',num_threads,'-o',out_file,bam_file
    ]
    (stdout,stderr) = run_command(" ".join([str(x) for x in command]))
    return (stdout,stderr)

def build_minimap_index():
    return

def map_reads(reference,readset,prefix,out_bam,num_threads=1):
    '''

    :param reference:
    :param readset:
    :param prefix:
    :param out_bam:
    :param num_threads:
    :return:
    '''
    command = ['minimap2', "-ax", "map-ont", "-t",num_threads,reference,readset,'|',
    'samtools', 'view', "-S", "-b","-F", "4", '|',
    'samtools', 'sort', '-@',num_threads,"-T",prefix,"--reference", reference,'-o',out_bam]
    (stdout,stderr) = run_command(" ".join([str(x) for x in command]))
    return (stdout,stderr)

def run_bedtools_coverage(bam_file):
    command = ['bedtools','genomecov','-bam',bam_file,'-d']
    (stdout,stderr) = run_command(" ".join([str(x) for x in command]))
    return (stdout, stderr)

def parse_bedtools(bed_tools_result):
    data = {}
    #TODO decode and parse the string from bedtools cov
    return data


def run():

    #Check dependencies
    pkg_resources.require(dependencies)

    #input parameters
    cmd_args = parse_args()
    test_data_fastq = cmd_args.test_data
    control_data_fastq = cmd_args.control_data
    ref_db_fasta = cmd_args.db
    adapt_sample_report_file = cmd_args.sample_report
    is_excluded = cmd_args.exclude
    outdir = cmd_args.outdir
    prefix = cmd_args.prefix
    perform_classification = cmd_args.classify
    num_threads = cmd_args.num_threads
    keep_tmp = cmd_args.keep_tmp
    degbug = cmd_args.debug
    dedup = cmd_args.dedup
    min_length = cmd_args.min_length
    max_length = cmd_args.max_length

    if degbug:
        logger = init_console_logger(4)
    else:
        logger = init_console_logger(3)


    #validate parameters
    error_status = False
    if not is_non_zero_file(test_data_fastq ):
        logger.ERROR("Test fastq data file {} does not exist or is empty".format(test_data_fastq))
        error_status = True
    if control_data_fastq is not None and not is_non_zero_file(control_data_fastq ):
        logger.ERROR("Control fastq data file {} does not exist or is empty".format(control_data_fastq))
        error_status = True
    if not is_non_zero_file(ref_db_fasta ):
        logger.ERROR("Reference fasta data file {} does not exist or is empty".format(ref_db_fasta))
        error_status = True
    if adapt_sample_report_file is not None and not is_non_zero_file(adapt_sample_report_file ):
        logger.ERROR("Adaptive sampling data file {} does not exist or is empty".format(adapt_sample_report_file))
        error_status = True

    if error_status:
        logger.ERROR("There is an issue with one or more of your input files, please check and try again")
        sys.exit()

    num_cpus = psutil.cpu_count(logical=False)
    if num_threads > num_cpus:
        num_threads = num_cpus

    # Initialize directory
    if not os.path.isdir(outdir):
        logger.info("Creating analysis directory {}".format(outdir))
        os.mkdir(outdir, 0o755)


    #Preprocess reads
    fastp_base_dir = os.path.join(outdir,"fastp")
    if not os.path.isdir(fastp_base_dir):
        logger.info("Creating analysis directory {}".format(fastp_base_dir))
        os.mkdir(outdir, 0o755)

    fastp_test_dir = os.path.join(fastp_base_dir, "test")
    if not os.path.isdir(fastp_test_dir):
        logger.info("Creating analysis directory {}".format(fastp_test_dir))
        os.mkdir(fastp_test_dir, 0o755)

    test_json = run_fastp(test_data_fastq, fastp_test_dir, 'test', min_read_len=min_length, max_read_len=max_length,
              report_only=False, dedup=dedup, n_threads=num_threads)

    if control_data_fastq is not None:
        fastp_control_dir = os.path.join(fastp_base_dir, "control")
        if not os.path.isdir(fastp_control_dir):
            logger.info("Creating analysis directory {}".format(fastp_control_dir))
            os.mkdir(fastp_control_dir, 0o755)

        control_json = run_fastp(control_data_fastq, fastp_control_dir, 'control', min_read_len=min_length, max_read_len=max_length,
                  report_only=False, dedup=dedup, n_threads=num_threads)

    # Processed Read Paths
    fastp_test_fastq = os.path.join(fastp_test_dir, "test.fastp.fastq")
    fastp_control_fastq = None
    if control_data_fastq is not None:
        fastp_control_fastq = os.path.join(fastp_control_dir, "control.fastp.fastq")


    #Run Nanoplot
    nanoplot_base_dir = os.path.join(outdir,"nanoplot")
    if not os.path.isdir(nanoplot_base_dir):
        logger.info("Creating analysis directory {}".format(nanoplot_base_dir))
        os.mkdir(nanoplot_base_dir, 0o755)

    nanoplot_test_dir = os.path.join(nanoplot_base_dir, "test")
    if not os.path.isdir(nanoplot_test_dir):
        logger.info("Creating analysis directory {}".format(nanoplot_test_dir))
        os.mkdir(nanoplot_test_dir, 0o755)

    run_nanoplot(fastp_test_fastq, nanoplot_test_dir, prefix, read_type='1D', num_threads=1)

    if control_data_fastq is not None:
        nanoplot_control_dir = os.path.join(nanoplot_base_dir, "control")
        if not os.path.isdir(nanoplot_control_dir):
            logger.info("Creating analysis directory {}".format(nanoplot_control_dir))
            os.mkdir(nanoplot_control_dir, 0o755)

        run_nanoplot(fastp_control_fastq, nanoplot_control_dir, prefix, read_type='1D', num_threads=1)

    #Map Reads
    logger.INFO("Mapping test reads {} to {} database".format(fastp_test_fastq,ref_db_fasta))
    minimap_base_dir = os.path.join(outdir,"minimap")
    if not os.path.isdir(minimap_base_dir ):
        logger.info("Creating analysis directory {}".format(minimap_base_dir ))
        os.mkdir(minimap_base_dir , 0o755)

    test_bam = os.path.join()
    (stdout,stderr) =  map_reads(ref_db_fasta, fastp_test_fastq, "{}-{}".format(prefix,random.randint(1,10000)), test_bam, num_threads)

    control_bam = None
    if control_data_fastq is not None:
        logger.INFO("Mapping control reads {} to {} database".format(fastp_control_fastq, ref_db_fasta))
        control_bam = os.path.join()
        (stdout, stderr) = map_reads(ref_db_fasta, fastp_control_fastq, "{}-{}".format(prefix,random.randint(1,10000)), control_bam, num_threads)


    #convert reads to fastq
    mapped_test_fastq = os.path.join(minimap_base_dir,"test.mapped.fastq")
    convert_bam_to_fastq(test_bam,mapped_test_fastq,num_threads)

    if control_bam is not None:
        mapped_control_fastq = os.path.join(minimap_base_dir,"control.mapped.fastq")
        convert_bam_to_fastq(control_bam,mapped_control_fastq,num_threads)


    #Calculate coverage of reference database




    # stub  test_cov_result = parse_bedtools(run_bedtools_coverage(test_bam_file))
    # stub  control_cov_result = parse_bedtools(run_bedtools_coverage(control_bam_file))




    return

# call main function
if __name__ == '__main__':
    run()