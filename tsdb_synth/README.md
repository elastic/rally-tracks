## TSDB k8s query track

The main goal of the TSDB TSID HASH track is to measure the performance of TSID hashing both at index and query time.
The dataset is synthetic and has been crafted to include many dimensions with different dimension name length and value size.

### Generated data

Generated data has the following characteristics:
* Includes about 3.5 hours of data with about 256 time series per second. Per each epoch a complete set of all time series is generated with timestamps calculated to be in a small range of less than 1 second so to have data more distributed over time other then generating all time series at the same point in time.
* Each time series is identified by a set of dimensions, one default `def_dim` dimension used as the `routing path` and 128 more dimensions whose names and values are
  randomly generated. Names are generated with different lenghts while values are generated with lengths such that the total aggregated size of all dimensions per each
  time series is (sometimes) larger then 32 Kb. The name of each dimension field starts with the prefix `d_` and ends with a progressive value as a suffix such as `001`, `002` and so on.
* Other then the timestamp field and dimension fields, data includes two metric fields, a gauge `gauge` and a counter `counter` and two non-metric fields, `key` and `val`

### Mapping properties

```json
{
    "properties": {
        "@timestamp": {
            "type": "date"
        },
        "def_dim": {
            "type": "keyword",
            "time_series_dimension": "true"
        },
        "counter": {
            "type": "long",
            "time_series_metric": "counter"
        },
        "gauge": {
            "type": "double",
            "time_series_metric": "gauge",
        },
        "key": {
            "type": "keyword"
        },
        "val": {
            "type": "integer"
        },
        "d_ufseibmjnkguynqfyclevvweebkoxqgvspbbngkvtrsegqtwuyel_001": {"type": "keyword", "time_series_dimension": "true"},
        "d_xnbbwadzlsmascuwfgmgezvpqdpxlhdbthcppsajhqbsakeyuhxoaiatvqrryxq_002": {"type": "keyword", "time_series_dimension": "true"},
        "d_blzajgeqnkncwuxcvtynuzkzopovmspftvxsdctqebzuomkiwjcieo_003": {"type": "keyword", "time_series_dimension": "true"},
        "d_qqnjuveqimaxewfvzdzardfuacdpiaitamagmvibwf_004": {"type": "keyword", "time_series_dimension": "true"},
        "d_xipvxrsjoijnsuevivtolfykfocpfssuvmcfpsyt_005": {"type": "keyword", "time_series_dimension": "true"},
        "d_akjodkyqfl_006": {"type": "keyword", "time_series_dimension": "true"},
        "d_nnwotohljrhizujqcrtkxgmlsrmapuoriceoahjmjcxfqauloo_007": {"type": "keyword", "time_series_dimension": "true"},
        "d_cadwiklfhhxnbepowpaoeexvdijgyhzaloxwrmvddctbcumvm_008": {"type": "keyword", "time_series_dimension": "true"},
        "d_rxkywkwqguca_009": {"type": "keyword", "time_series_dimension": "true"},
        "d_eisgvcnksbawsvd_010": {"type": "keyword", "time_series_dimension": "true"},
        "d_wbgmzlirkitlvhgpziaihplhoneywqajuaurcnksivljjanmubmgswzkw_011": {"type": "keyword", "time_series_dimension": "true"},
        "d_bjcrwryofdaefmutnmtycncwnp_012": {"type": "keyword", "time_series_dimension": "true"},
        "d_tmdopgrw_013": {"type": "keyword", "time_series_dimension": "true"},
        "d_dnysvciuvgtqgkeeqcuuffpnpiqumehnkkfchidmkacmef_014": {"type": "keyword", "time_series_dimension": "true"},
        "d_trmmtvdzuglsnbutbuylldxmpyvioh_015": {"type": "keyword", "time_series_dimension": "true"},
        "d_qtotzmjpdvrholegtddixzmhuklxpfkwdnqwicggtvuigppyzrovqf_016": {"type": "keyword", "time_series_dimension": "true"},
        "d_jdokldxavpnsrmdedowxerks_017": {"type": "keyword", "time_series_dimension": "true"},
        "d_hupbcujkmlecyeqixxuttowzctihnbexraglwwrixvdod_018": {"type": "keyword", "time_series_dimension": "true"},
        "d_aqcxnjgteaazeywfa_019": {"type": "keyword", "time_series_dimension": "true"},
        "d_vzawzvycpgzqjncnnvkmuwinzyaroepfyzfdnhvgen_020": {"type": "keyword", "time_series_dimension": "true"},
        "d_ppmjbulaiztsnhlcafqxmnaqtrkortvrhyxnylvtebslysmjzqvlxmeutyjrby_021": {"type": "keyword", "time_series_dimension": "true"},
        "d_uwkxqgjcagzfkgscpnkd_022": {"type": "keyword", "time_series_dimension": "true"},
        "d_aooyeqoyxulxzrliepbrgzxxbpjsybnsifurktorcjufj_023": {"type": "keyword", "time_series_dimension": "true"},
        "d_rkjjdrnfrihsybkzauxvuyn_024": {"type": "keyword", "time_series_dimension": "true"},
        "d_zzjvqkhnfuyjqmfyqycevcwrhxqkdvgfkvtxfdt_025": {"type": "keyword", "time_series_dimension": "true"},
        "d_egoqbcrosickbczvyubmtgwehqwcjsskwkinrppfids_026": {"type": "keyword", "time_series_dimension": "true"},
        "d_nsietpfxulkyrcyzscaasqlmdzktpou_027": {"type": "keyword", "time_series_dimension": "true"},
        "d_xtkktnwqqpvbcorrfvxbcyinwlupjozrkmtewwzlgagswwiqhruqzujxojtue_028": {"type": "keyword", "time_series_dimension": "true"},
        "d_gqxiwdeqjnccmzifzsavjlodzhccyzzsqopwzqvejgrbcsywpyetkpsehxwff_029": {"type": "keyword", "time_series_dimension": "true"},
        "d_glmaozbqzpgmtvcrjutdmfc_030": {"type": "keyword", "time_series_dimension": "true"},
        "d_pkvmdemjmfqzpaxxtiwypfclqpnltyvngxfjljsvkwxgapisjyvihlzrydgtl_031": {"type": "keyword", "time_series_dimension": "true"},
        "d_vearqgikeibzckvljimabmtrgyacygtmzidufsnrruuxbkkhndkuiran_032": {"type": "keyword", "time_series_dimension": "true"},
        "d_dpbpucerm_033": {"type": "keyword", "time_series_dimension": "true"},
        "d_kgglppzibjgtilurxllbeeannpgmjupwosd_034": {"type": "keyword", "time_series_dimension": "true"},
        "d_mfcwnfpwfiivsrpofmkfaddhktppfvfoq_035": {"type": "keyword", "time_series_dimension": "true"},
        "d_icykvfpdxfqlaoqliamasxbaaoxixlwagovgfvuhtfx_036": {"type": "keyword", "time_series_dimension": "true"},
        "d_dxynmwoxwtbeilsnmdbsordapgjmoetkijslzugydyjpnxfbgnwirjsjcm_037": {"type": "keyword", "time_series_dimension": "true"},
        "d_bpksasvwxerwnwbuilzgvomsejcwvirkgikxymfbmdxovzjrqccsdavkess_038": {"type": "keyword", "time_series_dimension": "true"},
        "d_fbskkemblnpczurtbabaomiezpulzjqbu_039": {"type": "keyword", "time_series_dimension": "true"},
        "d_zljayrez_040": {"type": "keyword", "time_series_dimension": "true"},
        "d_vyflfcdkqaqmzzafrwpsijldmnznekeeyclgqgyscfmwjgpjebxdisobvuzowzg_041": {"type": "keyword", "time_series_dimension": "true"},
        "d_bplubclwrchjkurzuhyiafioenrnprgghebiaygggrkguqcihtxl_042": {"type": "keyword", "time_series_dimension": "true"},
        "d_mwyuwbmyqjjuqvxhtgxpkbdalevlbtjowkfsm_043": {"type": "keyword", "time_series_dimension": "true"},
        "d_zszslmzdkjictecjcjvrwfmnw_044": {"type": "keyword", "time_series_dimension": "true"},
        "d_orgqbnoltihxfrghmqhfjdjpxskzpkdtovkyjsqagsmglwnjrymhmbxwwega_045": {"type": "keyword", "time_series_dimension": "true"},
        "d_mfalfoicnoodvcvftkicuztnbcbrwkhwicupjkrcqgezsstj_046": {"type": "keyword", "time_series_dimension": "true"},
        "d_pvqnuxsuaajhpsdlqpcawwpuvsjwvswrqgpkrqpcaumv_047": {"type": "keyword", "time_series_dimension": "true"},
        "d_gupwiidxrmpoptpzg_048": {"type": "keyword", "time_series_dimension": "true"},
        "d_ezvzczzzkabvuepjnrjt_049": {"type": "keyword", "time_series_dimension": "true"},
        "d_agmgfljrkslzymtjsqsxckuamkfkfmpsihyuvkdxvrcxyrvglwrcq_050": {"type": "keyword", "time_series_dimension": "true"},
        "d_pfwxfjkpwkyoomzlfmcerdpqcmwbbnigqodmbyevvehcsvsger_051": {"type": "keyword", "time_series_dimension": "true"},
        "d_qjjrgdicrrbb_052": {"type": "keyword", "time_series_dimension": "true"},
        "d_ayssroaqgoimnavyzohoqirjunvxfrvuqbroecpltibcujmigywq_053": {"type": "keyword", "time_series_dimension": "true"},
        "d_xnzfyznysgokvlcvhburbgqwjfjzy_054": {"type": "keyword", "time_series_dimension": "true"},
        "d_ktgforazlqhrvgzvadyszuzkqqljjehnceylojxuqq_055": {"type": "keyword", "time_series_dimension": "true"},
        "d_ebxhkvisfyddafshzteafrpbpyxrcylvtnqvtpuyrbsoc_056": {"type": "keyword", "time_series_dimension": "true"},
        "d_orsmhbwikbcwfxcmzskqdaqissfwilxrnzjynvrgceoptqpmjkgammmg_057": {"type": "keyword", "time_series_dimension": "true"},
        "d_iyvedzjtmpclftsopznfipqdgidhdihd_058": {"type": "keyword", "time_series_dimension": "true"},
        "d_mdyqxhdovbabgevnathxsqdvolqpadzfsoyeqcmsrrufhkxvmkwrabeisika_059": {"type": "keyword", "time_series_dimension": "true"},
        "d_dvhkskmzmvtbaqtuimlgxkdmevrvkvbdoozqzstvdaccgizdxegcismuohvydv_060": {"type": "keyword", "time_series_dimension": "true"},
        "d_wfhzvefualtakquglnvnfprgjuvrdlqzoegbxceawutkqmmmcsaftxciffjo_061": {"type": "keyword", "time_series_dimension": "true"},
        "d_wzxuxyzjrrhnuvknbwdbxcxxziscojebtkaqvtrftohxselpshaxj_062": {"type": "keyword", "time_series_dimension": "true"},
        "d_evgytuyrdqdhbcwijozzmeqtrnyvyqoqzsmp_063": {"type": "keyword", "time_series_dimension": "true"},
        "d_xhfoxicrnpkbtqwphinpcwhdkcpbgqlpzonmmhoymrwlojatsu_064": {"type": "keyword", "time_series_dimension": "true"},
        "d_erfsrejpcqazbbplfslaajubskdhcibmw_065": {"type": "keyword", "time_series_dimension": "true"},
        "d_vvejaixmuxnnnxpnwnmregbwnkptblapykgzdczlpidoxqno_066": {"type": "keyword", "time_series_dimension": "true"},
        "d_vegcmknltgrkfrxlmqzurpkuuhmiuiikpxzrcid_067": {"type": "keyword", "time_series_dimension": "true"},
        "d_lxxhbhtcvzkoeswmoxizlkgzbfcthzepnrfvflfuwgyxypoujvvpsovaedlxigt_068": {"type": "keyword", "time_series_dimension": "true"},
        "d_synpuqsgphcjhbuvnjjesqzwkdadikxqci_069": {"type": "keyword", "time_series_dimension": "true"},
        "d_mlouyrisesaywnuxwctwuzupoopsrylgpvtsg_070": {"type": "keyword", "time_series_dimension": "true"},
        "d_gstjsaggntqwugbzikeksujuyt_071": {"type": "keyword", "time_series_dimension": "true"},
        "d_jsxyvyvgffldldyconidbtyfrvnisqsviychbaghpqdzzjz_072": {"type": "keyword", "time_series_dimension": "true"},
        "d_slmlekdogwuyznlfzvflifsuxonfigpxyhpcadxof_073": {"type": "keyword", "time_series_dimension": "true"},
        "d_zcxqaqfebivrbpnhgm_074": {"type": "keyword", "time_series_dimension": "true"},
        "d_rgugqihpjcxlhglimkxruzpgzmcusnqwmnrzkfjahetbqpbtrmenudxnp_075": {"type": "keyword", "time_series_dimension": "true"},
        "d_wucgvjqlfgupikliqfbqzrhicewcz_076": {"type": "keyword", "time_series_dimension": "true"},
        "d_jfmfmjzsoluwljufgzdlskazqxjenjuzlyqoiavpcntzghonrlp_077": {"type": "keyword", "time_series_dimension": "true"},
        "d_wyldzmvvrvjbkielxdbyjythgrahlwvgkxcubcajmeoearrikakmcsthdke_078": {"type": "keyword", "time_series_dimension": "true"},
        "d_iarzgzcozvmkubufwrdwwuhhpbopdqhmbjiecpbbhdgrrkuhivhfsyni_079": {"type": "keyword", "time_series_dimension": "true"},
        "d_rrdutmsokqmomnhtctniorumhjxuwpmpbuswhbdktuissmfcpzbrcxndntxn_080": {"type": "keyword", "time_series_dimension": "true"},
        "d_qxaccsklvqjebsjwfbxnjcdnlhmoizvllxvkz_081": {"type": "keyword", "time_series_dimension": "true"},
        "d_dklsivejoouqdcl_082": {"type": "keyword", "time_series_dimension": "true"},
        "d_rolvyswdillwdausp_083": {"type": "keyword", "time_series_dimension": "true"},
        "d_myqckvrvsmncbudocvixuewjywrkcdkscam_084": {"type": "keyword", "time_series_dimension": "true"},
        "d_pluxuunglukbgjzcfaztqrhkngxdpfbicbgvxpcgpoamsrlswr_085": {"type": "keyword", "time_series_dimension": "true"},
        "d_mlamwfmidvxhwohrtypcxwnvmlxfqviwqpexdoly_086": {"type": "keyword", "time_series_dimension": "true"},
        "d_tswgxygdchjyqchjgncnrjhrzewhfusgfuavqjpttgy_087": {"type": "keyword", "time_series_dimension": "true"},
        "d_mkxjegmjlzkkwzuaagket_088": {"type": "keyword", "time_series_dimension": "true"},
        "d_jvzcvudaqy_089": {"type": "keyword", "time_series_dimension": "true"},
        "d_ndljtwayqimwxvpv_090": {"type": "keyword", "time_series_dimension": "true"},
        "d_pdbrwzfkxdigwojaslwkoyhwdpuybvsowivjbuwkldkadtaxbros_091": {"type": "keyword", "time_series_dimension": "true"},
        "d_eqahosohrurcs_092": {"type": "keyword", "time_series_dimension": "true"},
        "d_djlimaqszvyheetenvrevzgnkrrtsxsl_093": {"type": "keyword", "time_series_dimension": "true"},
        "d_kmpejulimytkrjczozfghforsychlbaysbrwrecfbawujny_094": {"type": "keyword", "time_series_dimension": "true"},
        "d_nbslhdzmdeqanexovwmjgkocvrg_095": {"type": "keyword", "time_series_dimension": "true"},
        "d_egldfzguunvjvoe_096": {"type": "keyword", "time_series_dimension": "true"},
        "d_kmhhervu_097": {"type": "keyword", "time_series_dimension": "true"},
        "d_kalqxdkiwtedrorvvrolmxwp_098": {"type": "keyword", "time_series_dimension": "true"},
        "d_ckxrhzavmsumfrnggqimvfoymzjguvpjanjctlwjlyegaiohikad_099": {"type": "keyword", "time_series_dimension": "true"},
        "d_xzvgddcctnwfhpebzkxgruzrcfjadtwchikthvsvce_100": {"type": "keyword", "time_series_dimension": "true"},
        "d_qudmdawmeyctcipeottybgepwerwitmrirnilvrcgxgyuntnrehmpnepcam_101": {"type": "keyword", "time_series_dimension": "true"},
        "d_tpuknqhtrar_102": {"type": "keyword", "time_series_dimension": "true"},
        "d_xhuhjbuevjylmmyoztqcqsdfmsbkttxxcgxyqgust_103": {"type": "keyword", "time_series_dimension": "true"},
        "d_hftdsrzzdrbtmbska_104": {"type": "keyword", "time_series_dimension": "true"},
        "d_pakcihdwycgvpsvtrqheavgspqkyxrkd_105": {"type": "keyword", "time_series_dimension": "true"},
        "d_aznyanfwxokcomewgfcjpe_106": {"type": "keyword", "time_series_dimension": "true"},
        "d_yarvhfrpetlhvpcaolhslhymgkwkhmmjlwlhnimvv_107": {"type": "keyword", "time_series_dimension": "true"},
        "d_adsloyvqxcithmxkigtgttlhmfxfmxkbjddyeqgrimblwjdse_108": {"type": "keyword", "time_series_dimension": "true"},
        "d_nbgwlbtqnperafzfrdshrisjvinagydmanucoebstqslbupqftrpsgqtc_109": {"type": "keyword", "time_series_dimension": "true"},
        "d_eomnifgshvuj_110": {"type": "keyword", "time_series_dimension": "true"},
        "d_ttmpvutlcbddpachzoavrrakgcjfmqqmarfvbpkhxtrqewd_111": {"type": "keyword", "time_series_dimension": "true"},
        "d_icgzivtjfwtrjtlmkxiayblroqujoapolpjldsrxuoiecdiiutys_112": {"type": "keyword", "time_series_dimension": "true"},
        "d_msrslyxeeioakoqtxarcejhmmaquoietjhneyks_113": {"type": "keyword", "time_series_dimension": "true"},
        "d_psybipczrhsymii_114": {"type": "keyword", "time_series_dimension": "true"},
        "d_cvciybuuydrodukczp_115": {"type": "keyword", "time_series_dimension": "true"},
        "d_rdmgfxyidmktyulcsdnehcsdkgqptzyqnjfuwgiksycxcjqvztolrwxnheiz_116": {"type": "keyword", "time_series_dimension": "true"},
        "d_ckgvgaiagassnuftbvm_117": {"type": "keyword", "time_series_dimension": "true"},
        "d_xgawtepdmjtclkfhnreoyrrpzrimxyrjbxsegdanrvmpxokkpgwmtsrnmg_118": {"type": "keyword", "time_series_dimension": "true"},
        "d_cfzzvuvzlldhfuudvgfz_119": {"type": "keyword", "time_series_dimension": "true"},
        "d_heonoqtezapfykjeafldgufpdzorgprayzmuqyomqxs_120": {"type": "keyword", "time_series_dimension": "true"},
        "d_vavkrppflewbbgpmbyi_121": {"type": "keyword", "time_series_dimension": "true"},
        "d_fdgpdkqfpoaohyfkvcftacp_122": {"type": "keyword", "time_series_dimension": "true"},
        "d_pisbrwfpvpcrwnawhlnvnfrgvholisawqa_123": {"type": "keyword", "time_series_dimension": "true"},
        "d_wrwvqjahlxmpybcfrqrqjhfqykfkuur_124": {"type": "keyword", "time_series_dimension": "true"},
        "d_faapharfxdlxuesunslqkfrmvvzggcgvtjbxedetojocnukhfxsoltckxsxhj_125": {"type": "keyword", "time_series_dimension": "true"},
        "d_zynorwvbvpusmwktuxkbulhbfcnnhtscqaetmbdvcpnbqkum_126": {"type": "keyword", "time_series_dimension": "true"},
        "d_ghfyoyozjwzgiwppedxemouhftmsakgjlyotbybommexuve_127": {"type": "keyword", "time_series_dimension": "true"},
        "d_dvretyeczsbaiabqdxrkdfwgneifefnxedasvwcshjeirqdrvyj_128": {"type": "keyword", "time_series_dimension": "true"}
    }
}
```

### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 5000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `enable_more_dimensions` (default: false)
