
<start> ::= <scenario>

<scenario> ::= "{\"num_connections\": " <num_connections> ", \"header_interval\": " <header_interval> ", \"attacker\": \"" <attacker> "\", \"target_server\": \"" <target_server> "\", \"duration_s\": " <duration_s> "}"

<num_connections> ::= <num_conn>
<num_conn> ::= r'[1-9][0-9]{0,2}' | '500'

<header_interval> ::= <num_interval>
<num_interval> ::= r'[1-9]' | r'[12][0-9]' | '30'

<attacker> ::= "h1" | "h2"

<target_server> ::= "python" | "php" | "java"

<duration_s> ::= <num_dur>
<num_dur> ::= r'[1-5][0-9]' | '10' | '60'

where int(<num_connections>) >= 1 and int(<num_connections>) <= 500
where int(<header_interval>) >= 1 and int(<header_interval>) <= 30
where int(<duration_s>) >= 10 and int(<duration_s>) <= 60
