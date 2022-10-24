LOG_FORMAT = '%(asctime)s %(name)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'

dependencies = [
  'pandas>=1.3.5',
  'numpy>=1.21.5',
]


report_header = [
  'sample_id',
  'analysis_date'
  'test_file_path',
  'control_file_path',
  'reference_db_path',
  'reference_db_md5',
  'mode',
  'db_id',
  'raw_test_num_reads',
  'raw_control_num_reads',
  'raw_test_num_bases',
  'raw_control_num_bases',
  'raw_test_n50',
  'raw_control_n50',
  'fastp_test_num_reads',
  'fastp_control_num_reads',
  'fastp_test_num_bases',
  'fastp_control_num_bases',
  'fastp_test_n50',
  'fastp_control_n50',
  'mapped_test_num_reads',
  'mapped_control_num_reads',
  'mapped_test_num_bases',
  'mapped_control_num_bases',
  'mapped_test_n50',
  'mapped_control_n50',

]



