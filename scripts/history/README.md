# Pipeline history

These are the scripts that produced Arbor Mono 1.2 to 2.5.1 from Noto
Serif's static TTFs. They are kept for provenance. Each `vX.Y/`
folder holds the refinement pass for that version. The release notes
in `documentation/design/RELEASE-NOTES-1.x-2.5.txt` describe each pass.

They are not part of the current build. From 2.501 on, the UFO files in
`sources/` are the design sources. Many of these scripts expect system
Noto fonts and hard-coded paths from the machines they were written on.
