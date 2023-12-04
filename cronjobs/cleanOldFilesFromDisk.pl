#! /usr/local/bin/perl

use strict;
use warnings;

select STDERR; $| = 1; select STDOUT; $| = 1;
my $cmd0 = "df -h /data/user/rlaher/sbx";
print "Executing [$cmd0]...\n";
my @op0 = `$cmd0`;
if (@op0) { print "Output from [$cmd0]=[@op0]\n"; }


my $dir1 = "/data/user/rlaher/sbx/L0";
&removeOldSubDirs(3, $dir1);


my $dir2 = "/data/user/rlaher/sbx/2D";
&removeOldSubDirs(3, $dir2);

my $dir3 = "/data/user/rlaher/sbx/masters/wlpixelfiles";
&removeOldFiles(5, $dir3);

my $cmd1 = "df -h /data/user/rlaher/sbx";

print "Executing [$cmd1]...\n";
my @op1 = `$cmd1`;
if (@op1) { print "Output from [$cmd1]=[@op1]\n"; }


#------------------------------------------
# Remove subdirectories under input directory that
# are older than N days, and all files therein.

sub removeOldSubDirs {

    my ($ndaysold, $dir) = @_;

    print "dir = $dir\n";
    opendir(DIR, "$dir"); 
    my @files = readdir DIR; 
    closedir DIR; 
    foreach my $file (@files) {
        print "file = $file\n";
        if (($file eq ".") or ($file eq "..") or ($file =~ /\.+/)) {
          print "Skipping file---->[$file]\n";
        }
        $file = $dir . "/" . $file;
        if ((-d $file) and (! ($file =~ /^.+\/\..*$/))) {
            my $fileage = -M $file;
            if ($fileage > $ndaysold) {
                print "Removing directory---->[$file]\n";  
                `rm -rf $file`;
            }
        }
    }
}


#------------------------------------------
# Remove files under input directory that
# are older than N days.

sub removeOldFiles {

    my ($ndaysold, $dir) = @_;

    print "dir = $dir\n";
    opendir(DIR, "$dir"); 
    my @files = readdir DIR; 
    closedir DIR; 
    foreach my $file (@files) {
        print "file = $file\n";
        if (($file eq ".") or ($file eq "..") or ($file =~ /\.+/)) {
          print "Skipping file---->[$file]\n";
        }
        $file = $dir . "/" . $file;
        if ((-f $file) and (! ($file =~ /^.+\/\..*$/))) {
            my $fileage = -M $file;
            if ($fileage > $ndaysold) {
                print "Removing file---->[$file]\n";  
                `rm -rf $file`;
            }
        }
    }
}



