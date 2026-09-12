/*
 * WIRS builtin YARA pack — assinaturas sintéticas e inertes.
 *
 * Regras aqui descrevem TÉCNICAS (padrões de bytes), nunca malware funcional:
 * os fixtures que as disparam são amostras sintéticas sem backend real.
 * Compilação validada no CI com yara-python (ver docs/providers/yara-python.md).
 */

rule WIRS_PHP_Webshell_EvalChain {
  meta:
    description = "PHP webshell-like: eval combinado com cadeia de decoding"
    severity = "high"
  strings:
    $eval = "eval(" ascii
    $b64 = "base64_decode(" ascii
    $inflate = "gzinflate(" ascii
  condition:
    filesize < 5MB and $eval and 1 of ($b64, $inflate)
}

rule WIRS_PHP_Dynamic_Include {
  meta:
    description = "include com variavel derivada de input (sintetica)"
    severity = "medium"
  strings:
    $get = "$_GET" ascii
    $include_var = "include $" ascii
  condition:
    filesize < 5MB and all of them
}
