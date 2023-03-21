const lyrics0 = "ここに歌詞を入力してください";
const lyrics1 = "きらきらひかる　おそらのほしよ\nまばたきしては　みんなをみてる\nきらきらひかる　おそらのほしよ\n";
const lyrics2 = "うさぎ追いしかの山\nこぶな釣りしかの川\n夢は今もめぐりて\nわすれがたきふるさと\n";

var words = ['ディズニー', 'サッカー', '駅名', '国名', '動物', 'オリジナルの単語リストを使う'];
var wordsId = ['word0','word1', 'word2', 'word3', 'word4', 'word5'];

const convertedLyrics0 = "歌詞を選択してください";
const convertedLyrics1 = "白木　ライアル　コドララド　星野　樽崎　重田　稲尾　李　テル　崔　八木彬　呂";
const convertedLyrics2 = "宇佐美　大井　鹿野　張\n小塚　辻功　河\nシューメーカー　岩郷　出口　陳\n";

function insertLyrics() {//選択された歌詞をテキストボックスに表示
    let song = document.getElementById('select-song').value;

    if (song == 'song1'){
        document.getElementById('input-lyrics').value = lyrics1;
    }else if (song == 'song2'){
        document.getElementById('input-lyrics').value = lyrics2;
    }else{
        document.getElementById('input-lyrics').value = lyrics0;
    }
}

function setWord1() {//セレクトボックスから単語を選択・ブロックの色を変更
    let word = document.getElementById('select-word').value;
    console.log(word);

    let selected = 0;
    let setColor;

    for (let i=0; i < words.length; i++){
        setColor = document.getElementById(wordsId[i]);
        setColor.style.background = "#00bfff";

        if (word == wordsId[i]){
            selected = i;
            console.log(i);
        }
    }

    let wordId = document.getElementById(wordsId[selected]);
    wordId.style.background = "#4169e1";
}

function setWord2(num) {//ブロックから単語を選択・ブロックの色を変更
    let word = document.getElementById('select-word').value;
    let setColor;

    for (let i=0; i < words.length; i++){
        setColor = document.getElementById(wordsId[i]);
        setColor.style.background = "#00bfff";
    }

    setColor = document.getElementById(wordsId[num]);
    setColor.style.background = "#4169e1";

    document.getElementById('select-word').innerHTML = '<option value=' + wordsId[num] + '>' + words[num] + '</option>';
}

function convert() {//替え歌をテキストボックスに出力 この関数はデモの時にのみ使用
    /*
    let song = document.getElementById('select-song').value;

    if (song == 'song1'){
        document.getElementById('output-lyrics').value = convertedLyrics1;
    }else if (song == 'song2'){
        document.getElementById('output-lyrics').value = convertedLyrics2;
    }else{
        document.getElementById('output-lyrics').value = convertedLyrics0;
    }
    */
}