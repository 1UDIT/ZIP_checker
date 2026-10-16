ARCHIVE CHECKER - Windows / Remote Network Shares

1. Install Python 3 and 7-Zip on the Windows PC running this program.
2. Edit config.json:
   archive_folders = folder(s) containing RAR/ZIP files. UNC shares supported.
   report_folder = local or shared location for CSV and LOG results.
   seven_zip_path = location of 7z.exe on this PC.
   recursive = true to include subfolders.
3. Ensure this Windows account can read each network share and its files.
4. Double-click run_checker.bat, or run:
      py -3 archive_checker.py --config config.json
5. Open the CSV in Excel; status OK means 7-Zip validated the archive.

EXAMPLE REMOTE FOLDER: \\192.168.1.100\MediaArchive\RAR
If access fails, open the UNC path in Windows Explorer and verify permissions.
For a share requiring separate credentials, authenticate beforehand from Windows:
   net use \\192.168.1.100\MediaArchive /user:DOMAIN\username *
Do not put network passwords into config.json.

Status notes:
OK - test passed.
FAILED - 7-Zip reported archive corruption/unsupported format/other error.
PASSWORD_OR_ENCRYPTED - archive cannot be fully validated without a password.
TIMEOUT - per-file test exceeded configured seconds.
ERROR - process/file system error.
FOLDER_UNAVAILABLE - folder is missing or access is denied.

For split RAR archives, place all volumes together (e.g. .part1.rar, .part2.rar).
Each .rar part matching extensions may be tested separately; other volume names
(such as .r00) are not scanned independently. Avoid modifying archives while checking.
The program reads files and does NOT extract them.
