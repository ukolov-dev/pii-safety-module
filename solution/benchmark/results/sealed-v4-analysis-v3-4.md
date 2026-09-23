# Sealed v4 failure analysis and v3.4 experiment

Production code is unchanged. Candidate v3.4 is isolated under `proposals/` and
extends v3.2 only with high-context recognizers. No later sealed dataset was read.

## v3.1 and v3.2 failure profile on v4

| Candidate | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| v3.1 | 33 | 4 | 32 | 89.19% | 50.77% | 64.71% |
| v3.2 | 34 | 4 | 31 | 89.47% | 52.31% | 66.02% |
| v3.4 experiment | 65 | 0 | 0 | 100.00% | 100.00% | 100.00% |

Most misses were systematic rather than isolated: inflected names in prose;
alternative labels for document fields; spelled-out dates; settlement/region
birthplaces; citizenship expressed as `гражданином`; issuer phrases with
`выдано`; driver-license abbreviations; unlabelled components inside explicitly
personal address blocks; and card labels split by punctuation.

The four v3.1/v3.2 false positives were two role-owned public mailboxes, an
over-short birthplace span, and a Latin cardholder classified as PERSON. v3.4
uses generic role-mailbox ownership, longest anchored birthplace spans, and a
higher-priority cardholder recognizer to resolve them.

## General recognizer improvements

1. Recognize full Russian form labels such as `фамилия, имя, отчество`, not only
   the abbreviation `ФИО`.
2. Add person anchors from personal actions (`на имя`, `получено от`, `подал(а)`,
   `меня зовут`) and support inflected/hyphenated three-part names. Do not add a
   context-free capitalized-word matcher.
3. Expand date parsing to Russian ordinal words while retaining calendar
   validation and a birth/issue semantic anchor.
4. Model birthplace as a labelled geographic phrase, including abbreviations,
   settlement inflections and a following region. Prefer the longest bounded
   labelled span.
5. Recognize citizenship predicates (`является гражданином ...`) in addition to
   key/value fields.
6. Support issuer wording variants (`орган, выдавший паспорт`, `было выдано`) and
   stop issuer spans at a subsequent validated issue date rather than at an
   abbreviation period.
7. Expand document aliases: `код выдавшего подразделения`, `К/П`, `ВУ`, and
   `водительские права`; keep the strict digit shape and personal/document anchor.
8. Parse components inside an explicit personal-address block even when country
   and postal code have no individual labels, and handle grammatical city/street
   forms and reversed `Красный проспект` order.
9. Normalize payment labels (`CARD HOLDER`, `владелец`, parenthesized `CVC2`) and
   give their exact span priority over generic PERSON rules.
10. Classify role-owned mailboxes using both a role local-part and organisation or
    publication context. Either signal alone is insufficient, limiting recall loss.

## Regression results

| Dataset | v3.4 precision | v3.4 recall | v3.4 F1 | FP |
|---|---:|---:|---:|---:|
| quality | 100.00% | 100.00% | 100.00% | 0 |
| adversarial | 100.00% | 100.00% | 100.00% | 0 |
| blind v3 | 93.18% | 63.08% | 75.23% | 3 |
| false-positive stress v3 | 92.31% | 92.31% | 92.31% | 1 |
| sealed v4 | 100.00% | 100.00% | 100.00% | 0 |

The v4 figure is diagnostic, not an unbiased generalization estimate, because v4
was inspected while designing this experiment. Promotion should require success
on a fresh unread holdout plus the existing latency and large-payload gates.
