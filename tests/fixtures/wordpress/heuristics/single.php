<?php
// Fixture: base64 isolado (uso legítimo comum) — sem finding sozinho.
$data = base64_decode($stored);
save($data);
