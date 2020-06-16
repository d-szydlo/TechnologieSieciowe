#!/usr/bin/perl

use HTTP::Daemon;
use HTTP::Status;  
use IO::File;

my $d = HTTP::Daemon->new(LocalAddr => 'localhost', LocalPort => 4321,)|| die;
  
print "Please contact me at: <URL:", $d->url, ">\n";

while (my $c = $d->accept) {
    while (my $r = $c->get_request) {
        if ($r->method eq 'GET') {  
            my $h = $r->headers_as_string;
            my $resp = HTTP::Response->new(200);
            $resp->header("Content-Type" => "text/plain");
            $resp->content($h);
            $c->send_response($resp);
        }
        else {
            $c->send_error(RC_FORBIDDEN);
        }
    }
    $c->close;
    undef($c);
}
