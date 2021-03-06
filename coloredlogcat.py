#!/usr/bin/python

'''
    Copyright 2015, Jag Saund

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
'''

# Color coded logcat script to highlight adb logcat output for console.

import io
import os
import re
import shutil
import sys

# pattern to extract data from log
# the pattern currently conforms to the log output received from
# adb 1.0.31
PATTERN = "^(\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}\.\d{3}) ([VDIWEFS])\/(.*)(\(\s*\d+\)):(.*)$"

# formatting properties

LOG_LEVEL_SILENT = '\033[0;38;5;255;48;5;248m'
LOG_LEVEL_SILENT_TEXT = '\033[0;38;5;248m'
LOG_LEVEL_VERBOSE = '\033[0;38;5;255;48;5;36m'
LOG_LEVEL_VERBOSE_TEXT = '\033[0;38;5;36m'
LOG_LEVEL_INFO = '\033[0;38;5;255;48;5;40m'
LOG_LEVEL_INFO_TEXT = '\033[0;38;5;40m'
LOG_LEVEL_DEBUG = '\033[0;38;5;255;48;5;33m'
LOG_LEVEL_DEBUG_TEXT = '\033[0;38;5;33m'
LOG_LEVEL_WARNING = '\033[0;38;5;255;48;5;208m'
LOG_LEVEL_WARNING_TEXT = '\033[0;38;5;208m'
LOG_LEVEL_ERROR = '\033[0;38;5;255;48;5;124m'
LOG_LEVEL_ERROR_TEXT = '\033[0;38;5;124m'
LOG_LEVEL_FATAL = '\033[0;38;5;255;48;5;196m'
LOG_LEVEL_FATAL_TEXT = '\033[0;38;5;196m'
LOG_PROCESS = '\033[0;38;5;36;48;5;236m'
LOG_TAG = '\033[0;38;5;255;48;5;236m'
LOG_TIMESTAMP = '\033[0;38;5;134m'
RESET = '\033[0m'

# column widths
WIDTH_LOG_LEVEL = 3
WIDTH_PID = 6
WIDTH_TIMESTAMP = 12
HEADER_SIZE = WIDTH_TIMESTAMP + 1 + WIDTH_PID + 1 + WIDTH_LOG_LEVEL + 1

# log level formatting
LOG_LEVEL_FORMATTING = {
    'S': LOG_LEVEL_SILENT,
    'V': LOG_LEVEL_VERBOSE,
    'I': LOG_LEVEL_INFO,
    'D': LOG_LEVEL_DEBUG,
    'W': LOG_LEVEL_WARNING,
    'E': LOG_LEVEL_ERROR,
    'F': LOG_LEVEL_FATAL
}

LOG_LEVEL_FORMATTING_TEXT = {
    'S': LOG_LEVEL_SILENT_TEXT,
    'V': LOG_LEVEL_VERBOSE_TEXT,
    'I': LOG_LEVEL_INFO_TEXT,
    'D': LOG_LEVEL_DEBUG_TEXT,
    'W': LOG_LEVEL_WARNING_TEXT,
    'E': LOG_LEVEL_ERROR_TEXT,
    'F': LOG_LEVEL_FATAL_TEXT
}

def format(text, width, format_prop=None, align='left'):
    if align == 'center':
        text = text.center(width)
    elif align == 'right':
        text = text.rjust(width)
    elif align == 'left':
        text = text.ljust(width)
    if format_prop:
        text = format_prop + text + RESET
    return text

def wrap_text(text, buf, indent=0, width=80):
    text_length = len(text)
    wrap_length = width - indent
    pos = 0
    while pos < text_length:
        next = min(pos + wrap_length, text_length)
        buf.write(text[pos:next])
        if next < text_length:
            buf.write("\n%s" % (" " * indent))
        pos = next
    wraped_text = buf.getvalue()

def extractPID(package):
    # attempt to extract the process ID from adb shell
    # if there is no pid associated with the package name then return None
    input = os.popen("adb shell ps | grep %s" % package)
    try:
        line = input.readline()
    except:
        return None
    else:
        if not line:
            return None
        return line.split()[1]
    finally:
        input.close()

def main():
    # get the current terminal width
    width = shutil.get_terminal_size().columns

    retag = re.compile(PATTERN)
    pid = None
    if len(sys.argv) > 1:
        package = sys.argv[1]
        pid = extractPID(package)

    proc = None

    # if someone is piping in to us, use stdin as input.  if not, invoke adb logcat
    if os.isatty(sys.stdin.fileno()):
        cmd = "adb logcat -v time"
        pipe = os.popen(cmd)
    else:
        pipe = sys.stdin

    while True:
        try:
            line = pipe.readline()
            if not line:
                break
        except KeyboardInterrupt:
            break
        except UnicodeError:
            continue
        except Exception as err:
            print(err)
            break
        else:
            match = retag.match(line)
            if match:
                date, timestamp, tagtype, tag, procID, message = match.groups()
                procID = procID[1:-1].strip()
                if pid and procID != pid:
                    continue

                tag = tag.strip()

                linebuf = io.StringIO()
                linebuf.write(format(timestamp, WIDTH_TIMESTAMP, LOG_TIMESTAMP, 'center') + " ")
                linebuf.write(format(procID, WIDTH_PID, LOG_PROCESS, 'center') + " ")
                linebuf.write(format(tagtype, WIDTH_LOG_LEVEL, LOG_LEVEL_FORMATTING[tagtype], 'center') + " ")
                linebuf.write(format(tag + ":", len(tag), LOG_TAG, '') + " ")
                tagTypeFormatting = LOG_LEVEL_FORMATTING[tagtype] if tagtype == "F" else LOG_LEVEL_FORMATTING_TEXT[tagtype]
                wrap_text(tagTypeFormatting + message + RESET, linebuf, HEADER_SIZE + 1 + len(tag) + 1, width)

                print(linebuf.getvalue())
                linebuf.close()
        finally:
            if proc:
                proc.terminate()


if __name__ == "__main__":
    main()

