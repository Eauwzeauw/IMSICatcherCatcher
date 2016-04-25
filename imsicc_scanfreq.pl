#!/usr/bin/perl

################################################################################
# imsicc_scanfreq.pl
# IMSI Catcher^2 or IMSI Catcher Catcher
# Script by Ben Hup
# Copyright (c) 2016 Ben Hup
# Created date 4 March 2016 v0.001
# Revised date 5 March 2016 v0.01
# Revised date 7 March 2016 v0.02
# Revised date 19 March 2016 v0.03 - by Piotr Tekieli
# Revised date 24 March 2016 v0.04 - by Andy Chiu
# Description: scan for frequencies in the GSM900 / GSM-R band for any GSM tower.
#		so real towers and IMSI-catchers; Any tower traffic will be picked up.
# Dependency: /usr/local/bin/grgsm_scanner
#
# Problem statement: Not all cell towers will be detected unless you execute 'problem solving'
# Problem solving:
#	step 1: run 'sudo nano /usr/local/bin/grgsm_scanner'
#	step 2: Change first line from: "#!/usr/bin/python2" to "#!/usr/bin/python2 -u"
#	Explanation: now Python will write unbuffered output to STDOUT, not missing any output/towers
################################################################################

use strict;
use warnings;
use DBI;

my $dbfile   = "imsicc.db";
my $dsn      = "dbi:SQLite:dbname=$dbfile";
my $user     = "";
my $password = "";
my $dbh = DBI->connect($dsn, $user, $password, {
PrintError       => 0,
RaiseError       => 1,
AutoCommit       => 1,
FetchHashKeyName => 'NAME_lc',
});

my $sql = <<'END_SQL';
CREATE TABLE IF NOT EXISTS towers (
	id			INTEGER PRIMARY KEY AUTOINCREMENT,
	frequency		UNSIGNED INTEGER(10),	/* 800 MHz to 1900 MHz, so 10 digits max */
	arfcn			UNSIGNED INTEGER(5),
	lai_mcc			UNSINGED INTEGER(3),	/* max 3 digits: mobile country code */
	lai_mnc			UNSINGED INTEGER(3),	/* 2 to 3 digits: mobile network code */
	lai_lac			UNSINGED INTEGER(5),	/* 16 bit, thus max 5 digits: location area code */
	cellid			UNSINGED INTEGER(5),	/* 16 bit, thus max 5 digits: unique in lac */
	neighbourcells		VARCHAR(255),	/* space delimited list of neighbour ARFCN's */
	signalstrength		INTEGER(4),	/* in dBm (because weak signal signed; often NEGATIVE!) */
	asksreauth		INTEGER(1),
	selectivehandover	INTEGER(1),
	nohandover		INTEGER(1),
	usedencryption		TEXT, 	/* ENUM("A5/0", "A5/1", "A5/2", "A5/3"), */
		/* or make usedencryption a VARCHAR and paste tshark string */
	nmea			TEXT,	/* VARCHAR(255) */,
	nrrejects		INTEGER(7),
	nrupdates		INTEGER(7),
	nrciphercommands	INTEGER(7),
	
	latitude	TEXT, /* VARCHAR(255) */
	longitude TEXT, /* VARCHAR(255) */
	recordadded		TEXT,	/* DATETIME */
	recordrevised		TEXT,	/* DATETIME */
	pcapngtower		INTEGER(1),
	reselection_offset		INTEGER(7),
	temporary_offset		INTEGER(7),
)
END_SQL
$dbh->do($sql) || die $_;

## show current content database
#my $sql = 'SELECT * FROM roguetowers';
#my $sth = $dbh->prepare($sql);
##$sth->execute();
##while (my @row = $sth->fetchrow_array) {
##	print "fname: $row[0]  lname: $row[1]\n";
##}
#$sth->execute();
#while (my $row = $sth->fetchrow_hashref) {
##	print "fname: $row->{fname}  lname: $row->{lname}\n";
#	foreach my $key (keys $row){
#		print "$key: ".$row->{$key}." ";
#	}
#	print "; ";
#}
#exit;

my $countround = 0;
print "Start scanning for cell towers (e.g. real ones and IMSI catchers)...\n";

while(1==1){ # infinite loop
	# Example grgsm_scanner output
	# ARFCN: 1022, Freq:  934.6M, CID: 63283, LAC:   225, MCC: 204, MNC:   4, Pwr: -27
	#  |---- Configuration: 1 CCCH, not combined
	#  |---- Cell ARFCNs: 59, 987, 988, 1004
	#  |---- Neighbour Cells: 975, 976, 978, 979, 983, 984, 995, 999, 1000, 1004, 1005, 1006, 1015, 1017, 1018, 1020, 1021, 1023

	$countround++;
	print '-==[ Scan round: '.$countround." ]==-\n";
	print ".\n";

	#Do one scan on R-GSM band and another with default option (P-GSM) for getting all towers
	for (my $i=1; $i <= 2; $i++) {

		my $arfcn = '';
		my $signalstrength = '';
		my $lai_lac = '';
		my $lai_mcc = '';
		my $lai_mnc = '';
		my $cellid = '';
		my $neighbourcells = '';
		my $frequency = '';

		my @scanner;
		#change to default option (P-GSM) after R-GSM has been scanned 
		if($i == 2) {
			print "-==[ Scanning with default band (P-GSM) ]==-\n";	
			@scanner = `/usr/local/bin/grgsm_scanner -v`;
		}
		else {
			print "-==[ Scanning with -b R-GSM ]==-\n";
			@scanner = `/usr/local/bin/grgsm_scanner -b R-GSM -v`;
		}


		foreach my $scanline (@scanner){
			$scanline =~ s/\r|\n//gi;
			my %scansplit = ();
	print $scanline."\n";
			if($scanline =~ m/^ARFCN\:\s/){
	print '1';
				%scansplit = split(/[\:\,]/, $scanline);
				foreach my $key (keys %scansplit){
					$scansplit{$key} =~ s/^\s+|\s+$//g; # strip spaces begin and end
					$scansplit{$key} =~ s/^\t+|\t+$//g;	   # strip tabs begin and end
					my $trimmedkey = lc($key);
					$trimmedkey =~ s/^\s+|\s+$//g;
					$trimmedkey =~ s/^\t+|\t+$//g;
					$scansplit{$trimmedkey} = $scansplit{$key};
				}
				$arfcn = $scansplit{'arfcn'};
				$signalstrength = $scansplit{'pwr'};
				$lai_lac = $scansplit{'lac'};
				$lai_mcc = $scansplit{'mcc'};
				$lai_mnc = $scansplit{'mnc'};
				$cellid = $scansplit{'cid'};
				$frequency = $scansplit{'freq'};

				$frequency =~ s/M//gi;
				$frequency = $frequency * 1000000;
			}
			elsif($scanline =~ m/\|---- Neighbour Cells\: /){
	print '2';
				my @split = split(/Neighbour Cells\:/, $scanline);
				$neighbourcells = $split[1];
				$neighbourcells =~ s/^\s+|\s+$//g;
	#		}
	#		elsif(length($scanline) <= 0){
	print '3';
				$dbh->do('INSERT INTO towers (frequency, arfcn, lai_mcc, lai_mnc, lai_lac, cellid, neighbourcells, signalstrength) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
					undef,
					$frequency, $arfcn, $lai_mcc, $lai_mnc, $lai_lac, $cellid, $neighbourcells, $signalstrength);

				%scansplit = ();
				$arfcn = '';
				$signalstrength = '';
				$lai_lac = '';
				$lai_mcc = '';
				$lai_mnc = '';
				$cellid = '';
				$neighbourcells = '';
				$frequency = '';

				$dbh->disconnect;
				$dbh = DBI->connect($dsn, $user, $password, {
				PrintError       => 0,
				RaiseError       => 1,
				AutoCommit       => 1,
				FetchHashKeyName => 'NAME_lc',
				});
			}
		}
	}


}

$dbh->disconnect;

exit(0);


__END__

	my $fname = 'Foo';
	my $lname = 'Bar',
	my $email = 'foo@bar.com';
	$dbh->do('INSERT INTO people (fname, lname, email) VALUES (?, ?, ?)',
		undef,
		$fname, $lname, $email);

	my $password = 'hush hush';
	my $id = 1;
	$dbh->do('UPDATE people SET password = ? WHERE id = ?',
		undef,
		$password,
		$id);

	my $sql = 'SELECT fname, lname FROM people WHERE id >= ? AND id < ?';
	my $sth = $dbh->prepare($sql);
	$sth->execute(1, 10);
	while (my @row = $sth->fetchrow_array) {
		print "fname: $row[0]  lname: $row[1]\n";
	}
	$sth->execute(12, 17);
	while (my $row = $sth->fetchrow_hashref) {
		print "fname: $row->{fname}  lname: $row->{lname}\n";
	}
