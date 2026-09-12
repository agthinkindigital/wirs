/*
 * EXPERIMENTAL — desabilitado por default (from_pack sem experimental=True).
 * Regras aqui têm falso-positivo conhecido; promoção segue o processo de
 * maturidade do spec (experimental → beta → stable, §10.3).
 */

rule WIRS_EXP_PHP_Long_Encoded_Literal {
  meta:
    description = "EXPERIMENTAL: literal codificado longo (sintetica)"
    severity = "low"
    maturity = "experimental"
  strings:
    $long = /[A-Za-z0-9+\/=]{200,}/ ascii
  condition:
    filesize < 5MB and $long
}
