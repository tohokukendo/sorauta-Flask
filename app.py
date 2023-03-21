from flask import Flask, render_template, request
from flask_ngrok import run_with_ngrok
import uuid
from gensim.models import word2vec
import gensim
from gensim.models import KeyedVectors
import random
import dimod
from pyqubo import Array, Constraint, Placeholder
from dwave.system import DWaveCliqueSampler
from openjij import SQASampler
import process

app = Flask(__name__)
run_with_ngrok(app)  # Start ngrok when app is run

parody = "ここに替え歌が出力されます"
myword = "まだ選択されていません"

def convertLyrics(Lyrics, Words):

    #引数からLyricsを読み込み
    lyrics_array_temp = Lyrics.translate(str.maketrans({",":"", ".":"", "!":"", "?":""})).split()
    lyrics_array = []
    pos_l = 0
    pos_ipa_ja = 0

    #発音記号に変換
    l_ipa_array = process.eng2IPA(lyrics_array_temp)

    #日本語風IPAに変換
    l_ipa_ja_array = process.japanization(l_ipa_array)

    for idx in range(len(lyrics_array_temp)):
        l = lyrics_array_temp[idx]
        l_len = len(l)
        l_ipa = l_ipa_array[idx]
        l_ipa_ja = l_ipa_ja_array[idx]
        len_ipa_ja = len(l_ipa_ja)
        lyrics_array.append([idx, l, pos_l, l_len, l_ipa, l_ipa_ja, pos_ipa_ja, len_ipa_ja])
        pos_l += l_len
        pos_ipa_ja += len_ipa_ja

    #英語の歌詞（日本語風IPA化済み）を結合
    l_ipa_ja_all = ""
    for row in lyrics_array:
        l_ipa_ja_all += row[5]

    #word2vecの取り込み
    if dict_mode == WHITE_GOAT:
        model = word2vec.Word2Vec.load("word2vec/word2vec.gensim.model")
        vocab = model.wv.index2word

    #word2vecの取り込み
    if dict_mode == CHIVE:
        #  model = gensim.models.KeyedVectors.load('chive-1.2-mc15_gensim/chive-1.2-mc15.kv')
        #  model = gensim.models.KeyedVectors.load('chive-1.1-mc90_gensim/chive-1.1-mc90.kv')
        model = gensim.models.KeyedVectors.load('chive-1.1-mc90-aunit_gensim/chive-1.1-mc90-aunit.kv')
        vocab = model.wv.index2word

    #word2vecの取り込み
    if dict_mode == TOHOKU:
        model = KeyedVectors.load_word2vec_format('entity_vector/entity_vector.model.bin', binary=True)
        vocab = model.wv.index2word
    
    word_dict = process.prepareWordDict(vocab)

    #インスタンス生成
    k2IPA = process.Kana2IPA("Japanese-Phonetic-Notation/Dictionary/kana_to_eng.dic")
    
    #引数からkeywordを読み込み
    keyword = Words

    #word収集
    model.most_similar(keyword, topn=20)

    #空耳ワード辞書から歌詞と発音一致度が高いワードを抽出
    word_opt = process.getWordOpt(word_dict, l_ipa_ja_all, keyword, model)

    #ランダムで2000個を抽出
    MAX_WORDS = 2000
    if len(word_opt) > MAX_WORDS:
        words = random.sample(word_opt.MAX_WORDS)
    else:
        words = word_opt

    #空耳ワードの文字の重なりを評価
    C = process.makeCmat(words)

    #定式化モードの選択
    DIMOD = 1
    PYQUBO = 2
    formula_mode= PYQUBO

    if formula_mode == DIMOD:
        cqm = dimod.ConstrainedQuadraticModel()
        x = []
        for i in range(len(words)):
            x.append(dimod.Binary(f'x_{i}'))
    if formula_mode == PYQUBO:
        x = Array.create(name='x', shape=(len(words)), vartype='BINARY')
    
    #重み付け
    lam1 = 1
    lam2 = 1
    lam3 = 100

    #コスト関数
    if formula_mode == DIMOD:
        cqm.set_objective(\
            -lam1*sum(words[i][4]*x[i] for i in range(len(words)))\
            -lam2*sum(words[i][5]*x[i] for i in range(len(words)))\
            +lam3*sum(sum(C[i][j]*x[i]*x[j] for j in range(i+1,len(words))) for i in range(len(words)))\
            )   

    if formula_mode == PYQUBO:
        costA = -Placeholder('lam1')*sum(words[i][4]*x[i] for i in range(len(words)))
        costB = -Placeholder('lam2')*sum(words[i][5]*x[i] for i in range(len(words)))
        costC =  Placeholder('lam3')*sum(sum(C[i][j]*x[i]*x[j] for j in range(i+1,len(words))) for i in range(len(words)))

    #変換
    if formula_mode == PYQUBO:
        cost_func = costA + costB + costC
        pyModel = cost_func.compile()

    if formula_mode == DIMOD:
        bqm, invert = dimod.cqm_to_bqm(cqm,lagrange_multiplier=10)

    if formula_mode == PYQUBO:
        feed_dict = {'lam1': lam1, 'lam2': lam2, 'lam3': lam3}
        qubo, offset = pyModel.to_qubo(feed_dict=feed_dict)
    
    #Samplerの選択
    DWAVE = 1
    OPENJIJ = 2
    sampler_mode = OPENJIJ

    num_reads = 100
    if sampler_mode == DWAVE:
        from dwave.system import DWaveSampler, EmbeddingComposite
        token="DEV-92bfbd94d8862c6315dd32cc918c7bc6366091f1"
        #dw_sampler = DWaveSampler(solver='Advantage_system4.1', token=token)
        #sampler = EmbeddingComposite(dw_sampler)
        #Embeddingが終わらないので全結合で固定化
        sampler = DWaveCliqueSampler(solver='Advantage_system6.1', token=token)

        if formula_mode == DIMOD:
            sampleset = sampler.sample(bqm,num_reads = num_reads)
        if formula_mode == PYQUBO:
            sampleset = sampler.sample_qubo(qubo, num_reads=num_reads)

    if sampler_mode == OPENJIJ:
        sampler = SQASampler()
        sampleset = sampler.sample_qubo(qubo, num_reads=num_reads)
    
    res = sampleset.first.sample
    sora_word = []
    for i in range(len(res)):
        if res.get(f'x[{i}]',0) == 1:
            sora_word.append(words[i])
    sora_word = sorted(sora_word,key=lambda x:(x[6]))

    #結果の整形
    pos = 0
    res_ipa_1 = []
    res_ipa_2 = []
    res_ja_kana = []
    res_ja_kanj = []
    for s in sora_word:
        if pos < s[6]:
            res_ipa_1.append("*"*(s[6]-pos))
            res_ipa_2.append(" "*(s[6]-pos))
            res_ja_kana.append("*"*(s[6]-pos))
            res_ja_kanj.append("*"*(s[6]-pos))
            pos += s[6]-pos

        if pos == s[6]:
            res_ipa_1.append(s[2])
            res_ipa_2.append(" "*(len(s[2])))
            res_ja_kana.append(s[1])
            res_ja_kanj.append(s[0])
            pos += len(s[2])
  
        elif pos > s[6]:
            res_ipa_1.append(" "*(len(s[2])-(pos-s[6])))
            last = res_ipa_2.pop()
            res_ipa_2.append(" "*(len(last)-(pos-s[6])))
            res_ipa_2.append(s[2])
            res_ja_kana.append(s[1])
            res_ja_kanj.append(s[0])
            pos += len(s[2])-(pos-s[6])

    results = "".join(res_ja_kana)
    
    return results


@app.route("/", methods=["GET","POST"])
def index():
    if request.method == 'POST':
      id = uuid.uuid1()
      readlyrics = request.form.get('input-lyrics')
      myword = request.form.get('select-word')
      if myword == 'word0':
        myword == "ディスニー"
      else:
        myword == "アニマル"
      parody = convertLyrics(readlyrics,myword)
      return render_template("index.html",myword=myword,parody=parody)
    else:
      return render_template("index.html")

if __name__ == '__main__':
    app.run()