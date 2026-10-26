// Worker du site : sert les fichiers statiques de publication/.
// Seul ajout : une adresse qui se termine par « / » sert son index.html
// (les autres adresses, dont …/module.html, sont servies telles quelles).
export default {
  async fetch(requete, env) {
    const url = new URL(requete.url);
    if (url.pathname.endsWith("/")) {
      url.pathname += "index.html";
      return env.ASSETS.fetch(new Request(url, requete));
    }
    return env.ASSETS.fetch(requete);
  },
};
