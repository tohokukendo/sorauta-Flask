from phonemizer import phonemize
import Levenshtein
import pykakasi
import warnings
import re
import numpy as np

#英語の発音記号（IPA）を日本語の発音風に変換
def japanization(ipa):
  jdict2 = {'oʊ':'ɔː', 'əʊ':'ɔː', 'ɑː':'aː', 'ɜː':'aː', 'ʧ':'ty', 'tʃ':'ty', 'ʤ':'jy', 'dʒ':'jy'}
  jdict1 = {'ɪ':'i', 'ɛ':'e', 'æ':'a', 'ə':'a', 'ɚ':'aː', 'ɝ':'aː', 'ʊ':'u', 'ʌ':'a', 'ɒ':'ɔ', 'ŋ':'n',\
            'ɡ':'g', 'ɹ':'r', 'ɻ':'r', 'ʃ':'sy', 'θ':'s', 'ð':'z', 'v':'b', 'ɾ':'r'}

  rets = []
  for w in ipa:
    ret = w
    for key, value in jdict2.items():
      ret = ret.replace(key, value)
    rets.append(ret.translate(str.maketrans(jdict1)))
  return rets

#英単語を発音記号（IPA）に変換
def eng2IPA(word):

  return [x.strip() for x in phonemize(word, language='en-us', backend='espeak')]

#word2vecから抽出した単語一覧を下準備
#  0:元の単語（漢字）
#  1:変換後の単語（ひらがな）
#  2:発音記号（IPA風）
def prepareWordDict(vocab):
  warnings.filterwarnings('ignore')
  kakasi = pykakasi.kakasi() # インスタンスの作成
  kakasi.setMode('J', 'H') # 漢字をひらがなに変換するように設定
  conversion = kakasi.getConverter() # 上記モード設定の適用

  #日本語をIPA風に変換
  k2IPA = Kana2IPA("Japanese-Phonetic-Notation/Dictionary/kana_to_eng.dic")

  word_dict = []
  pattern = re.compile(r'[a-zA-Z0-9]+')
  for v in vocab:
    #英単語は除外
    if not pattern.fullmatch(v):
      w_hira = conversion.do(v)
      #ひらがな返還後の文字数が３文字以上のみ使用
      if len(w_hira) > 2:
        w_ipa = "".join(k2IPA.convert(w_hira))
        word_dict.append([v, w_hira, w_ipa])
  
  return word_dict

#空耳ワード辞書から歌詞と発音一致度が高いワードを抽出
#  0:元の単語（漢字）
#  1:変換後の単語（ひらがな）
#  2:発音記号（IPA風）
#  3:切り出した歌詞（日本語風IPA）
#  4:レーベンシュタイン距離の一致率
#  5:空耳ワードとキーワードとの一致度
#  6:結合済み英語の歌詞（日本語風IPA化済み）の位置
def getWordOpt(word_dict, l_ipa_ja_all, keyword, model):
  import Levenshtein
  CRITERIA_LEVEN = 0.39
  CRITERIA_SIMIL = 0.4
  word_opt = []
  for j in range(len(word_dict)):
    #空耳ワードの1.5倍の長さで一致度評価
#    ext = len(word_dict[j])//2
    ext = 0
    for i in range(len(l_ipa_ja_all) - len(word_dict[j][2]) - ext):
      text = l_ipa_ja_all[i:i+len(word_dict[j][2]) + ext]
      #レーベンシュタイン距離の測定
      r = Levenshtein.ratio(text, word_dict[j][2])
      #短い単語ほど一致率が高くなるように空耳ワードの文字数の逆数を条件に追加
      if r >= CRITERIA_LEVEN + 1/len(word_dict[j][2]):
        #空耳ワードとキーワードとの一致度取得
        sim = model.wv.similarity(keyword,word_dict[j][0])
        if sim >= CRITERIA_SIMIL:
          word_opt.append([word_dict[j][0], word_dict[j][1], word_dict[j][2], text, r, sim, i])
  return word_opt

#空耳ワードの文字の重なりを評価
def makeCmat(word_opt):
  N = len(word_opt)
  C = np.zeros((N, N))
  for i in range(N):
    for j in range(i+1, N):
      start_w_i = word_opt[i][6]                #ワードiの歌詞割り当て開始位置
      end_w_i = start_w_i + len(word_opt[i][2]) #ワードiの歌詞割り当て終了位置
      start_w_j = word_opt[j][6]                #ワードjの歌詞割り当て開始位置
      end_w_j = start_w_j + len(word_opt[j][2]) #ワードjの歌詞割り当て終了位置
  
      #重なっている場合は重なっている文字数を設定
      if end_w_i > start_w_j and start_w_i < end_w_j:
        C[i][j] = min(end_w_i,end_w_j) - max(start_w_i,start_w_j)

  return C

#ひらがな・カタカナを発音記号に変換
class Kana2IPA():
  #convert kana to IPA

  _MAX_LENGTH = 4

  _kana2IPA = {}
  _longVowel = set(["aa","ei","ii","oo","uu","ou","ee","ɔɔ","ɔu"]) 

  def __init__(self, dic_path):
    for line in open(dic_path):
      (key, value) = line.strip().split(" ")
      self._kana2IPA[key] = value
    
 
  def convert(self, words):
    rets = []
    for word in words:
      ret = []
      word_len = len(word)
      start_point = 0
      end_point = min(self._MAX_LENGTH, word_len)
      while(start_point < word_len):
        while(end_point >= start_point):
          if end_point == start_point:
            ret.append(sub)
            break
          
          sub = word[start_point:end_point]
          if sub in self._kana2IPA:
            ret.append(self._kana2IPA[sub])
            break
          else:
            end_point -= 1
        else:
          ret = "".join(sub) + word[start_point:]
        forward_len = len(sub)
        start_point += forward_len
        end_point = start_point + self._MAX_LENGTH if start_point + self._MAX_LENGTH < word_len else word_len
      
      if len(ret) >= 2:
        tmp = [ret[0]]
        for i in range(1, len(ret)):
          if ret[i-1][-1] + ret[i] in self._longVowel:
            tmp[-1] += "ː"
            i += 1
          else:
            tmp.append(ret[i])
        
        ret = tmp
      rets.append("".join([x.translate(str.maketrans({"ʃ":"s", "ʌ":"a", "-":"ː"})) for x in ret]))

    return rets