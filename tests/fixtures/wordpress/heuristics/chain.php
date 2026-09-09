<?php
// Fixture inerte (WIRS-055): cadeia encoding + execução dinâmica sem payload real.
// Lido apenas como bytes pelo teste. Sem eval: assert() já exercita a família.
assert(base64_decode(gzinflate('fixtureinerte')));
