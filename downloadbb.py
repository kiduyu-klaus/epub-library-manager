from best_download import download_file

url = "http://ipv4.download.thinkbroadband.com/10MB.zip"
checksum = "d076d819249a9827c8a035bb059498bf49f391a989a1f7e166bc70d028025135"
local_file = "10MB.zip"
try:
  success = download_file(url, local_file=local_file, expected_checksum=checksum)
except KeyboardInterrupt:
  print("Ctrl-C (SIGINT) is passed up")
#download_file(urls, expected_checksum=None, local_file=None, local_directory=None, max_retries=3)
