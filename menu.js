const LINKS=[["index.html","Início"],["calendario.html","Calendário"],["corridas.html","Corridas"],["pilotos.html","Pilotos"],["equipes.html","Equipes"],["circuitos.html","Circuitos"],["campeoes.html","Campeões"]];
const NAC={British:"Reino Unido",Dutch:"Países Baixos",Italian:"Itália",Monegasque:"Mônaco",Australian:"Austrália",French:"França","New Zealander":"Nova Zelândia",Argentine:"Argentina",German:"Alemanha",Brazilian:"Brasil",Spanish:"Espanha",Thai:"Tailândia",Japanese:"Japão",Canadian:"Canadá",Finnish:"Finlândia",Mexican:"México"};
function corEquipe(n){
  n=(n||"").toLowerCase();
  const m=[["mercedes","#27c4aa"],["ferrari","#e8002d"],["mclaren","#ff8000"],["racing","#6692ff"],["rb f1","#6692ff"],["red bull","#3671c6"],["alpine","#ff87bc"],["haas","#9a9ea5"],["audi","#d6224a"],["williams","#37bedd"],["aston","#229971"],["cadillac","#8a8a99"]];
  for(const [k,c] of m) if(n.includes(k)) return c;
  return "#888";
}
const lerDados=async n=>(await fetch("dados/"+n)).json();
document.addEventListener("DOMContentLoaded",()=>{
  const atual=location.pathname.split("/").pop()||"index.html";
  const h=document.createElement("header");
  h.className="topo";
  h.innerHTML='<div class="in"><a class="marca" href="index.html">F1 <b>BRASIL</b></a><nav>'+LINKS.map(([u,t])=>'<a href="'+u+'"'+(u===atual?' class="on"':"")+'>'+t+'</a>').join("")+'</nav></div>';
  document.body.prepend(h);
});
Object.assign(NAC,{Swiss:"Suíça",Belgian:"Bélgica",Austrian:"Áustria",Swedish:"Suécia",American:"Estados Unidos","South African":"África do Sul",Danish:"Dinamarca",Russian:"Rússia",Chinese:"China",Polish:"Polônia",Portuguese:"Portugal",Venezuelan:"Venezuela",Colombian:"Colômbia",Chilean:"Chile",Hungarian:"Hungria",Irish:"Irlanda","Rhodesian":"Rodésia",Indian:"Índia",Indonesian:"Indonésia",Liechtensteiner:"Liechtenstein",Uruguayan:"Uruguai",Czech:"Tchéquia",Malaysian:"Malásia","East German":"Alemanha Oriental"});
const GPS={Australian:"da Austrália",Chinese:"da China",Japanese:"do Japão",Bahrain:"do Bahrein","Saudi Arabian":"da Arábia Saudita",Miami:"de Miami",Canadian:"do Canadá",Monaco:"de Mônaco",Spanish:"da Espanha",Barcelona:"de Barcelona","Barcelona-Catalunya":"de Barcelona",Madrid:"de Madri",Austrian:"da Áustria",British:"da Grã-Bretanha",Belgian:"da Bélgica",Hungarian:"da Hungria",Dutch:"da Holanda",Italian:"da Itália",Azerbaijan:"do Azerbaijão",Singapore:"de Singapura","United States":"dos Estados Unidos","Mexico City":"da Cidade do México",Mexican:"do México","São Paulo":"de São Paulo","Sao Paulo":"de São Paulo","Las Vegas":"de Las Vegas",Qatar:"do Catar","Abu Dhabi":"de Abu Dhabi",Malaysian:"da Malásia",Emilia:"da Emília-Romanha","Emilia Romagna":"da Emília-Romanha"};
const nomeGP=n=>{const k=n.replace(" Grand Prix","");return "GP "+(GPS[k]||"de "+k)};
const PAIS={Australia:"Austrália",China:"China",Japan:"Japão",Bahrain:"Bahrein","Saudi Arabia":"Arábia Saudita",USA:"Estados Unidos",UAE:"Emirados Árabes",Monaco:"Mônaco",Canada:"Canadá",Spain:"Espanha",Austria:"Áustria",UK:"Reino Unido",Belgium:"Bélgica",Hungary:"Hungria",Netherlands:"Países Baixos",Italy:"Itália",Azerbaijan:"Azerbaijão",Singapore:"Singapura",Mexico:"México",Brazil:"Brasil",Qatar:"Catar",Malaysia:"Malásia",France:"França",Germany:"Alemanha",Portugal:"Portugal",Argentina:"Argentina","South Africa":"África do Sul",Turkey:"Turquia"};
const pais=c=>PAIS[c]||c;
