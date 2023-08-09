import json
import random

DOCUMENT_FIXED_LENGTH = 256
DOCUMENT_COUNT = 10000

with open("bert_vocab_whole_words.json") as word_file:
    word_list = json.load(word_file)

with open("../document_set.json", "w") as doc_file:
    for i in range(DOCUMENT_COUNT):
        doc_words = random.choices(word_list, k=DOCUMENT_FIXED_LENGTH)
        doc = {"body": " ".join(doc_words)}

        doc_file.writelines([json.dumps(doc), "\n"])



{"body":"Fifty-four per cent of people questioned in France over the issue want the mainly French-speaking southern region of Wallonia incorporated into France if a split with Dutch-speaking Flanders was to occur. Relations between France and Belgium are close.rench-speaking Belgium should become part of France in the event of a split with its Dutch-speaking half, a poll suggests.",
 "id":"4768250",
 "ml":{"tokens":{"german":0.36837044,"mostly":0.18526462,"belgian":1.2231177,"fifty":0.75433487,"whole":0.1317957,"dutch":1.6321746,"division":0.50052756,"speaking":0.18375981,"het":0.06054002,"english":0.12721182,"flemish":0.3010021,"majority":0.19162716,"because":0.15755855,"per":0.10583842,"95":0.012606221,"if":0.48934156,"plan":0.03219757,"french":1.5614251,"case":0.13952503,"splitting":0.91920674,"issue":0.36089486,"%":0.32577276,"want":0.6619342,"switzerland":0.56910247,"##ching":0.10288924,"population":0.5921924,"wanted":0.44932067,"integration":0.7915273,"formed":0.108627945,"become":0.55466324,"southern":1.2273694,"be":0.22416775,"regions":0.019748261,"independent":0.048684526,"south":0.5551738,"questioning":0.4753595,"##onia":1.5248479,"result":0.09583664,"into":0.2020106,"asked":0.6620578,"member":0.1682862,"share":0.33631366,"speak":0.18016994,"relationship":0.20432186,"event":0.20151907,"close":0.7071169,"europe":0.6545578,"question":1.0440209,"languages":0.6737013,"break":0.23413618,"joined":0.2730545,"union":0.304154,"consolidation":0.17521548,"people":0.36869302,"integrate":0.039254148,"culture":0.43123853,"future":0.08461727,"ask":0.046339583,"relations":0.78035647,"country":0.899313,"incorporation":0.78809035,"dialect":0.5918503,"separate":0.32587054,"republic":0.1627835,"cent":0.72435457,"friendly":0.015795939,"questions":0.6937938,"political":0.12154688,"language":1.0015682,"incorporate":0.533194,"poll":0.026420502,"independence":0.69715315,"mainly":0.50042576,"split":1.745574,"incorporated":1.134298,"percentage":0.58010185,"should":0.7817701,"france":1.5884169,"ren":1.2306454,"50":0.28642926,"communication":0.0024053708,"belgium":1.5861554,"border":0.6199722,"area":0.49576804,"england":0.22552319,"holland":0.515922,"occur":0.15656509,"european":0.6561074,"franco":0.04578084,"amsterdam":0.016690616,"netherlands":0.7205609,"brussels":0.61854106,"most":0.10738262,"proposed":0.02534576,"region":0.9198981,"conflict":0.035355534,"became":0.50113654,"euro":0.2676968,"colony":0.50217354,"united":0.027636154,"idea":0.20691794,"part":1.0567409,"divided":0.30004102,"percent":0.8736786,"integrated":1.0271024,"total":0.086899064,"paris":0.070118845,"##ch":1.1839122,"rate":0.44683933,"divide":0.24568404,"included":0.32277596,"possibility":0.07437543,"incorporating":0.0297503,"questioned":0.57156736,"flanders":1.6157678,"war":0.03186934,"urban":0.0047763777,"reunion":0.18320088,"wall":1.3599854,"merger":0.24753635,"compromise":0.08358293,"territory":0.7303025},
       "model_id":".elser_model_1"}}
