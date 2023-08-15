#!/usr/bin/perl

use strict;
use warnings;

use Dir::Self;
use File::Basename qw( basename dirname );
use JSON::MaybeXS;
use Log::Any qw($log);
use Path::Tiny;
use Template;
use Syntax::Keyword::Try;


my $json = JSON::MaybeXS->new(
    canonical     => 1,
    pretty        => 1,
    indent_length => 4
);

my $distroot = dirname(__DIR__);
my $api_calls_filename = "$distroot/deriv_api/deriv_api_calls.py";
my $streams_list_filename = "$distroot/deriv_api/streams_list.py";

chomp(my $date = qx( date +%Y%m%d-%H%M%S ));

my @methods;

sub emit_functions {
    my ($root) = @_;

    $root = path($root);

    # Helper for reporting on anything in the schema we can't handle
    my $check = sub {
        my $def = shift;
        die "non-object def - " . $def->{type} unless $def->{type} eq 'object';
        die "unexpected schema " . $def->{'$schema'} unless $def->{'$schema'} =~ m{http://json-schema.org/draft-0[34]/schema#};
    };

    # Expected path structure is $methodname/{send,receive}.json
    foreach my $dir (sort $root->children) {
        my $method = $dir->basename;

        $log->tracef("Applying method %s", $method);

        my ($send, $recv) = map {
            try {
                my $def = $json->decode(path($dir, $_ . '.json')->slurp_utf8);
                $check->($def);
                $def;
            }
            catch ($e) {
                die "$method $_ load/validation failed: $e"
            } 
        } qw(send receive);

        # NOTE: Some type definitions use arrays, we don't support that yet

        my $send_props = parse_properties($send);
        chomp(my $encoded_props = $json->encode($send_props));

        push @methods, {
            # the real api method name e.g. proposal_open_contract
            method => $method,
            # Any request that supports req_id will automatically get an ID and this will be used
            # in determining which response is which.
            has_req_id       => exists $send_props->{req_id},
            needs_method_arg => needs_method_arg($method, $send_props),
            description      => $send->{description},
            is_method        => exists $send_props->{$method},
            encoded_props    => $encoded_props =~ s/"/'/rg =~ s/\n/\n        /rg =~ s/ :/:/rg,
            props            => parse_properties($send, full => 1),
        };
    }
}

sub parse_properties {
    my $schema   = shift;
    my %options  = @_;
    my $props    = $schema->{properties};
    my @required = ($schema->{required} || [])->@*;
    my %data;
    for my $prop (keys %$props) {
        if (exists $props->{$prop}{properties}) {
            $data{$prop} = parse_properties($props->{$prop});
        } else {
            my $type;
            $type = 'numeric' if ($props->{$prop}{type} || '') =~ /^(?:number)$/;
            $type = 'integer' if ($props->{$prop}{type} || '') =~ /^(?:integer)$/;
            $type = $1        if ($props->{$prop}{type} || '') =~ /^(string|boolean)$/;
            my $description = $props->{$prop}->%{description};
            $description =~ s/`//g if $description;
            $data{$prop} = {
                $type ? (type => $type) : (),
                (grep { /^$prop$/ } @required) ? (required => 1) : (),
                $options{full} ? (description => $description) : (),
            };
        }
    }
    return \%data;
}

sub to_camel_case { shift =~ s/_(\w)/\U$1/rg }

sub needs_method_arg {
    my ($method, $send_props) = @_;

    # { "method": { "type": "integer", "enum": [1] } }
    return 1 unless my $enum = $send_props->{$method}{enum};

    return 0 if scalar($enum->@*) == 1 and $enum->[0] == 1;

    return 1;
}

emit_functions($ENV{BINARYCOM_API_SCHEMA_PATH} // '/home/git/binary-com/deriv-developers-portal/config/v3');

my $template = Template->new(
    INCLUDE_PATH => "$distroot/scripts/templates",
);

$template->process(
    "api-call-py.tt2",
    {
        scriptname => $0,
        date       => $date,
        methods    => \@methods,
    }, \my $output) or die $template->error . "\n";

path($api_calls_filename)->spew_utf8($output);

$output = '';
$template->process(
    'streams_list.py.tt2',
    {
        scriptname => $0,
        date       => $date,
        methods    => \@methods,
    }, \$output
) or die $template->error . "\n";

path($streams_list_filename)->spew_utf8($output);
