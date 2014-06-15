# A setup script showing advanced features.
#
# Note that for the NT service to build correctly, you need at least
# win32all build 161, for the COM samples, you need build 163.
# Requires wxPython, and Tim Golden's WMI module.

# Note: WMI is probably NOT a good example for demonstrating how to
# include a pywin32 typelib wrapper into the exe: wmi uses different
# typelib versions on win2k and winXP.  The resulting exe will only
# run on the same windows version as the one used to build the exe.
# So, the newest version of wmi.py doesn't use any typelib anymore.

from distutils.core import setup
import py2exe
import sys

# If run without args, build executables, in quiet mode.
if len(sys.argv) == 1:
    sys.argv.append("py2exe")
    sys.argv.append("-q")

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "0.5.0"
        self.company_name = "virtualpianist.com"
        self.copyright = "GPL Version 3"
        self.name = "Virtual Page Turner"

################################################################
# A program using wxPython

# The manifest will be inserted as resource into test_wx.exe.  This
# gives the controls the Windows XP appearance (if run on XP ;-)
#
# Another option would be to store it in a file named
# test_wx.exe.manifest, and copy it with the data_files option into
# the dist-dir.
#
manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
/>
<description>%(prog)s Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''

RT_MANIFEST = 24

vpt = Target(
    # used for the versioninfo resource
    description = "Virtual Page Turner",

    # what to build
    script = "vpt.py",
    other_resources = [(RT_MANIFEST, 1, manifest_template % dict(prog="vpt"))],
##    icon_resources = [(1, "icon.ico")],
    dest_base = "vpt")

setup(
    options = {"py2exe": {"typelibs":
                          # typelib for pdfwin and WMI
                          [('{565783C6-CB41-11D1-8B02-00600806D9B6}', 0, 1, 2),
                           ('{EAB22AC0-30C1-11CF-A7EB-0000C05BAE0B}', 0, 1, 1)],
                          # create a compressed zip archive
                          "compressed": 1,
                          "optimize": 2,
                          "excludes": []}},
    # The lib directory contains everything except the executables and the python dll.
    # Can include a subdirectory name.
    zipfile = "lib/shared.zip",
    data_files = ["Welcome.gif","GPL-license.txt",
                  "gpl-3.0-standalone.htm"],
    
    windows = [vpt],
    )

