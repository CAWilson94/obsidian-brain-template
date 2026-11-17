<%*
// Picks a random emoji not already used at the start of any note title (falls back to the full pool).
const pool = ["🌱","🪐","🦊","🍄","🧁","🪴","🐙","🧩","🔭","🛸","🍋","🦉","🧶","🪁","🐝","🍉","🧭","🪄","🦋","🍒","🐢","🎲","🧪","🪵","🐳","🍩","🎈","🦔","🌵","🔮","🥑","🐞","🫧","🦩","🍓","🪸","🐌","🍪","🎧","🛼"];
const names = app.vault.getMarkdownFiles().map((f) => f.basename);
const free = pool.filter((e) => !names.some((n) => n.startsWith(e)));
const list = free.length > 0 ? free : pool;
tR += list[Math.floor(Math.random() * list.length)];
%>
