// Emoji for the chat's emoji picker, by category. Each line is the emoji
// followed by the words it can be found with in the picker's search.
// (Kept here rather than loaded from another site, so the picker works
// offline and nobody else learns what people type.)

const RAW = {
  smileys: {
    label: 'Smileys',
    icon: '😀',
    list: `
😀 grinning smile happy
😃 smiley happy joy
😄 smile happy laugh
😁 grin beaming teeth
😆 laughing satisfied haha
😅 sweat smile relief phew
🤣 rofl rolling floor laughing lol
😂 joy tears laughing lol crying
🙂 slightly smiling
🙃 upside down silly sarcasm
😉 wink flirt
😊 blush smiling happy
😇 innocent halo angel
🥰 love hearts adore
😍 heart eyes love crush
🤩 star struck wow amazing
😘 kiss blowing love
😗 kissing
😚 kissing closed eyes
😋 yum delicious tasty tongue
😛 tongue playful
😜 winking tongue crazy joke
🤪 zany crazy goofy wild
😝 squinting tongue
🤑 money rich dollar
🤗 hug hugging
🤭 hand over mouth oops giggle
🤫 shush quiet secret
🤔 thinking hmm wonder
🤐 zipper mouth secret
🤨 raised eyebrow suspicious
😐 neutral meh
😑 expressionless blank
😶 no mouth speechless
😏 smirk smug
😒 unamused annoyed
🙄 eye roll whatever
😬 grimace awkward yikes
😮‍💨 exhale sigh relief
🤥 lying pinocchio
😌 relieved calm
😔 pensive sad
😪 sleepy tired
🤤 drooling
😴 sleeping zzz tired
😷 mask sick ill
🤒 thermometer fever sick
🤕 bandage hurt injured
🤢 nauseated sick gross
🤮 vomit sick puke
🤧 sneeze cold sick
🥵 hot sweating heat
🥶 cold freezing ice
🥴 woozy dizzy drunk
😵 dizzy knocked out
🤯 mind blown exploding wow
🤠 cowboy yeehaw
🥳 party celebrate birthday
🥸 disguise incognito
😎 cool sunglasses
🤓 nerd geek glasses
🧐 monocle curious inspect
😕 confused
😟 worried
🙁 frowning sad
😮 open mouth surprised wow
😯 hushed surprised
😲 astonished shocked
😳 flushed embarrassed
🥺 pleading puppy eyes please
🥹 holding back tears touched grateful
😦 frowning open mouth
😧 anguished
😨 fearful scared
😰 anxious sweat nervous
😥 sad relieved disappointed
😢 crying sad tear
😭 sobbing crying loudly
😱 screaming fear shocked omg
😖 confounded
😣 persevering struggle
😞 disappointed sad
😓 downcast sweat
😩 weary tired
😫 tired exhausted
🥱 yawn bored sleepy
😤 triumph huff proud steam
😡 pouting angry rage mad
😠 angry mad
🤬 cursing swearing angry
😈 devil smiling evil
👿 imp angry devil
💀 skull dead lol
☠️ skull crossbones danger
💩 poop
🤡 clown
👻 ghost boo halloween
👽 alien ufo
🤖 robot bot
😺 cat smiling
😹 cat joy tears
😻 cat heart eyes love
🙈 see no evil monkey shy
🙉 hear no evil monkey
🙊 speak no evil monkey oops
`,
  },
  gestures: {
    label: 'People',
    icon: '👋',
    list: `
👋 wave hello hi bye
🤚 raised back hand
🖐️ hand fingers splayed
✋ raised hand stop high five
🖖 vulcan spock
👌 ok perfect
🤌 pinched fingers italian
🤏 pinching small little
✌️ victory peace
🤞 crossed fingers luck hope
🫰 hand index thumb crossed money love
🤟 love you gesture
🤘 rock on horns metal
🤙 call me shaka
👈 point left
👉 point right
👆 point up
👇 point down
☝️ index up one
🫵 point at you
👍 thumbs up like yes good ok
👎 thumbs down dislike no bad
✊ raised fist
👊 fist bump punch
🤛 left fist bump
🤜 right fist bump
👏 clap applause bravo
🙌 raising hands celebrate hooray
🫶 heart hands love
👐 open hands
🤲 palms up together
🤝 handshake deal agree
🙏 pray please thanks folded hands namaste
✍️ writing
💅 nail polish
🤳 selfie
💪 muscle strong flex biceps
🧠 brain smart
👀 eyes look see
👁️ eye
👅 tongue
👄 mouth lips
🫦 biting lip
👶 baby
🧒 child kid
👦 boy
👧 girl
🧑 person adult
👨 man
👩 woman
🧓 older person
👴 old man grandpa
👵 old woman grandma
🙋 raising hand question me
🙅 no gesture stop
🙆 ok gesture
💁 tipping hand info
🤷 shrug dunno whatever
🤦 facepalm ugh
🙇 bowing sorry thanks
🧑‍💻 technologist coder developer laptop
🧑‍🍳 cook chef
🧑‍🎓 student graduate
🧑‍🏫 teacher
🧑‍⚕️ doctor health
🧑‍🎨 artist painter
🧑‍🚀 astronaut space
🦸 superhero
🧙 mage wizard
🏃 running run
🚶 walking walk
💃 dancing woman dance
🕺 dancing man dance
👯 party dancing friends
🧘 yoga meditation
🧗 climbing
🚴 cycling bike
🏊 swimming swim
👫 couple friends
👪 family
🗣️ speaking talk
👥 people group
`,
  },
  hearts: {
    label: 'Hearts',
    icon: '❤️',
    list: `
❤️ red heart love
🧡 orange heart
💛 yellow heart
💚 green heart
💙 blue heart
💜 purple heart
🤎 brown heart
🖤 black heart
🤍 white heart
🩷 pink heart
🩵 light blue heart
💔 broken heart sad
❤️‍🔥 heart on fire passion
❤️‍🩹 mending heart healing
❣️ heart exclamation
💕 two hearts love
💞 revolving hearts
💓 beating heart
💗 growing heart
💖 sparkling heart
💘 heart arrow cupid
💝 heart ribbon gift
💟 heart decoration
💌 love letter
💋 kiss lips
💯 hundred perfect score 100
💢 anger
💥 collision boom
💫 dizzy star
💦 sweat drops
💨 dash fast wind
🕳️ hole
💬 speech bubble chat
💭 thought bubble
🗯️ anger bubble
💤 zzz sleep
✨ sparkles shiny magic
⭐ star
🌟 glowing star
🔥 fire hot lit
⚡ lightning zap
🎉 party popper tada celebrate congrats
🎊 confetti ball celebrate
`,
  },
  nature: {
    label: 'Animals & nature',
    icon: '🐶',
    list: `
🐶 dog puppy
🐱 cat kitten
🐭 mouse
🐹 hamster
🐰 rabbit bunny
🦊 fox
🐻 bear
🐼 panda
🐨 koala
🐯 tiger
🦁 lion
🐮 cow
🐷 pig
🐸 frog
🐵 monkey
🐔 chicken
🐧 penguin
🐦 bird
🐤 chick baby bird
🦆 duck
🦅 eagle
🦉 owl
🦇 bat
🐺 wolf
🐴 horse
🦄 unicorn
🐝 bee honey
🐛 bug caterpillar
🦋 butterfly
🐌 snail slow
🐞 ladybug
🐢 turtle slow
🐍 snake
🦎 lizard
🐙 octopus
🦀 crab
🐠 fish tropical
🐬 dolphin
🐳 whale
🦈 shark
🐊 crocodile
🐘 elephant
🦒 giraffe
🐪 camel
🐕 dog
🐈 cat
🌵 cactus
🎄 christmas tree
🌲 evergreen tree
🌳 tree
🌴 palm tree beach
🌱 seedling plant grow
🌿 herb leaf
🍀 four leaf clover luck
🍁 maple leaf autumn fall
🍂 fallen leaves autumn
🌷 tulip flower
🌹 rose flower love
🌻 sunflower
🌸 cherry blossom flower spring
💐 bouquet flowers
🌞 sun face sunny
🌝 full moon face
🌙 crescent moon night
🌍 earth globe world
⛅ partly cloudy
🌧️ rain
⛈️ storm thunder
❄️ snowflake cold winter
☃️ snowman winter
🌈 rainbow
☀️ sun sunny
🌊 wave ocean sea
💧 droplet water
`,
  },
  food: {
    label: 'Food & drink',
    icon: '🍕',
    list: `
🍏 green apple
🍎 apple red
🍐 pear
🍊 orange tangerine
🍋 lemon
🍌 banana
🍉 watermelon
🍇 grapes
🍓 strawberry
🫐 blueberries
🍒 cherries
🍑 peach
🥭 mango
🍍 pineapple
🥥 coconut
🥝 kiwi
🍅 tomato
🥑 avocado
🍆 eggplant
🥕 carrot
🌽 corn
🌶️ hot pepper chili spicy
🥒 cucumber
🥦 broccoli
🧄 garlic
🧅 onion
🥔 potato
🍞 bread
🥐 croissant
🥖 baguette
🧀 cheese
🥚 egg
🍳 cooking fried egg breakfast
🥞 pancakes
🥓 bacon
🍗 chicken leg
🍖 meat
🌭 hot dog
🍔 burger hamburger
🍟 fries
🍕 pizza
🥪 sandwich
🌮 taco
🌯 burrito
🥗 salad healthy
🍝 spaghetti pasta
🍜 noodles ramen
🍲 stew pot
🍛 curry rice
🍣 sushi
🍱 bento
🥟 dumpling momo
🍚 rice
🍙 rice ball
🍤 shrimp
🍦 ice cream
🍩 doughnut donut
🍪 cookie
🎂 birthday cake
🍰 cake shortcake
🧁 cupcake
🍫 chocolate
🍬 candy
🍭 lollipop
🍿 popcorn movie
☕ coffee tea hot
🍵 tea green
🧋 bubble tea boba
🥤 soft drink soda
🧃 juice box
🥛 milk
🍺 beer
🍻 cheers beers
🥂 champagne toast cheers
🍷 wine
🍸 cocktail
🍹 tropical drink
`,
  },
  activities: {
    label: 'Activities',
    icon: '⚽',
    list: `
⚽ football soccer
🏀 basketball
🏈 american football
⚾ baseball
🥎 softball
🎾 tennis
🏐 volleyball
🏉 rugby
🏏 cricket
🏸 badminton
🏓 ping pong table tennis
🏒 hockey
⛳ golf
🥊 boxing
🥋 martial arts karate
🎯 target bullseye darts goal
🛹 skateboard
⛸️ ice skate
🎿 ski
🏋️ weight lifting gym
🤸 cartwheel gymnastics
⛹️ basketball player
🤾 handball
🏇 horse racing
🏄 surfing
🚣 rowing
🧗 climb
🚵 mountain biking
🏆 trophy win champion
🥇 gold medal first
🥈 silver medal second
🥉 bronze medal third
🏅 medal sports
🎖️ military medal
🎗️ ribbon
🎫 ticket
🎟️ admission tickets
🎪 circus tent
🎭 theatre masks drama
🎨 art palette paint
🎬 clapper movie film
🎤 microphone sing karaoke
🎧 headphones music
🎼 score music
🎹 piano keyboard
🥁 drum
🎷 saxophone
🎺 trumpet
🎸 guitar
🎻 violin
🎲 dice game
♟️ chess pawn
🧩 puzzle
🎮 video game controller gaming
🕹️ joystick arcade
🎳 bowling
🎰 slot machine
🎁 gift present
🎈 balloon party
🎀 ribbon bow
`,
  },
  travel: {
    label: 'Travel & places',
    icon: '✈️',
    list: `
🚗 car
🚕 taxi
🚌 bus
🚎 trolleybus
🏎️ racing car
🚓 police car
🚑 ambulance
🚒 fire engine
🚚 truck delivery
🚲 bicycle bike
🛵 scooter
🏍️ motorcycle
🛺 auto rickshaw
🚂 train locomotive
🚆 train
🚇 metro subway
✈️ airplane flight travel
🛫 departure takeoff
🛬 arrival landing
🚀 rocket launch space
🛸 ufo flying saucer
🚁 helicopter
⛵ sailboat
🚤 speedboat
🚢 ship cruise
⚓ anchor
⛽ fuel pump gas
🚦 traffic light
🗺️ map world
🧭 compass
🏔️ snow mountain
⛰️ mountain
🌋 volcano
🏕️ camping tent
🏖️ beach umbrella
🏜️ desert
🏝️ island
🏞️ national park
🏟️ stadium
🏛️ classical building museum
🏗️ construction
🏠 house home
🏡 house garden home
🏢 office building
🏥 hospital
🏦 bank
🏨 hotel
🏪 shop store
🏫 school
🏰 castle
🕌 mosque
🛕 hindu temple mandir
⛪ church
🗼 tower
🗽 statue of liberty
🌆 city dusk
🌃 night city
🌉 bridge night
🎡 ferris wheel
🎢 roller coaster
⛲ fountain
🗓️ calendar date
⏰ alarm clock time
⌛ hourglass time
`,
  },
  objects: {
    label: 'Objects',
    icon: '💡',
    list: `
⌚ watch
📱 phone mobile
💻 laptop computer
⌨️ keyboard
🖥️ desktop computer
🖨️ printer
🖱️ mouse computer
💾 floppy save
💿 cd disk
📷 camera photo
📸 camera flash photo
📹 video camera
🎥 movie camera film
📺 tv television
📻 radio
🔋 battery
🔌 plug
💡 bulb idea light
🔦 flashlight torch
🕯️ candle
💸 money flying
💵 dollar money cash
💰 money bag
💳 credit card
💎 gem diamond
⚖️ balance scale law
🔧 wrench tool fix
🔨 hammer tool
🛠️ tools
⚙️ gear settings
🧲 magnet
🔬 microscope science
🔭 telescope
📡 satellite antenna
💉 syringe vaccine
💊 pill medicine
🩺 stethoscope doctor
🚪 door
🛏️ bed sleep
🛋️ couch sofa
🚿 shower
🧼 soap clean
🛒 shopping cart
🎒 backpack school
👓 glasses
🕶️ sunglasses cool
👕 t-shirt shirt
👖 jeans
👗 dress
👟 sneaker shoe running
👑 crown king queen
🎓 graduation cap
🧢 cap hat
💍 ring wedding
📚 books study read
📖 book open read
📝 memo note write
✏️ pencil
🖊️ pen
📌 pushpin pin
📍 round pin location
📎 paperclip attach
✂️ scissors cut
📅 calendar date
📈 chart up increase growth
📉 chart down decrease
📊 bar chart stats
📋 clipboard
📁 folder
🗂️ dividers
📦 package box delivery
✉️ envelope mail
📧 email
📣 megaphone announce
📢 loudspeaker announcement
🔔 bell notification
🔕 no bell mute
🔒 lock locked secure
🔓 unlocked
🔑 key
🗝️ old key
🧸 teddy bear
🪄 magic wand
`,
  },
  symbols: {
    label: 'Symbols',
    icon: '✅',
    list: `
✅ check mark done yes
☑️ check box
✔️ check
❌ cross no wrong
❎ cross mark button
➕ plus add
➖ minus
➗ divide
✖️ multiply
❓ question
❔ white question
❗ exclamation important
❕ white exclamation
‼️ double exclamation
⁉️ exclamation question
⚠️ warning caution
🚫 prohibited no forbidden
⛔ no entry stop
🔴 red circle
🟠 orange circle
🟡 yellow circle
🟢 green circle
🔵 blue circle
🟣 purple circle
⚫ black circle
⚪ white circle
🟥 red square
🟩 green square
🟦 blue square
🔺 red triangle up
🔻 red triangle down
🔸 orange diamond
🔹 blue diamond
➡️ right arrow
⬅️ left arrow
⬆️ up arrow
⬇️ down arrow
↗️ up right arrow
🔄 repeat refresh
🔁 repeat loop
▶️ play
⏸️ pause
⏹️ stop
⏩ fast forward
🔀 shuffle
🔊 speaker loud volume
🔇 mute
🆕 new
🆓 free
🆗 ok button
🆒 cool button
🆙 up button
🆘 sos help
ℹ️ information info
🔞 eighteen adult
♻️ recycle
✳️ asterisk
❇️ sparkle
©️ copyright
®️ registered
™️ trademark
#️⃣ hashtag number
🔢 numbers
🎵 musical note music
🎶 notes music
💲 dollar sign
🏁 checkered flag finish race
🚩 red flag
🏳️ white flag
🏴 black flag
🏳️‍🌈 rainbow flag pride
🇮🇳 india flag
🇺🇸 united states usa flag
🇬🇧 united kingdom uk flag
🇨🇦 canada flag
🇦🇺 australia flag
🇩🇪 germany flag
🇫🇷 france flag
🇯🇵 japan flag
🇧🇷 brazil flag
🇳🇵 nepal flag
🇧🇩 bangladesh flag
🇱🇰 sri lanka flag
🇦🇪 uae emirates flag
`,
  },
};

// [{ id, label, icon, emoji: [{ char, words }] }]
export const EMOJI_CATEGORIES = Object.entries(RAW).map(([id, c]) => ({
  id,
  label: c.label,
  icon: c.icon,
  emoji: c.list
    .trim()
    .split('\n')
    .map((line) => {
      const space = line.indexOf(' ');
      return { char: line.slice(0, space), words: line.slice(space + 1).toLowerCase() };
    }),
}));

const ALL = EMOJI_CATEGORIES.flatMap((c) => c.emoji);

// Emoji whose words start with what was typed (each typed word must match).
export function searchEmoji(query, limit = 80) {
  const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.length) return [];
  const found = ALL.filter((e) => {
    const words = e.words.split(' ');
    return terms.every((t) => words.some((w) => w.startsWith(t)));
  });
  // Ones whose main name matches first ("fire" → 🔥 before ❤️‍🔥).
  const main = (e) => (e.words.split(' ')[0].startsWith(terms[0]) ? 0 : 1);
  return found.sort((a, b) => main(a) - main(b)).slice(0, limit);
}

// ---------- recently used (kept in this browser only) ----------

const RECENT_KEY = 'circle.chat.recentEmoji';
const RECENT_MAX = 24;

export function recentEmoji() {
  try {
    const list = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
    return Array.isArray(list) ? list.filter((x) => typeof x === 'string').slice(0, RECENT_MAX) : [];
  } catch {
    return [];
  }
}

export function rememberEmoji(char) {
  const list = [char, ...recentEmoji().filter((x) => x !== char)].slice(0, RECENT_MAX);
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(list));
  } catch {
    // private mode / storage full: just don't remember
  }
  return list;
}

// True when `text` is only 1-3 emoji (shown large, like other chat apps).
export function isBigEmoji(text) {
  const t = (text || '').trim();
  if (!t || t.length > 40) return false;
  if (!/^[\p{Extended_Pictographic}\p{Emoji_Component}‍️⃣\s]+$/u.test(t)) return false;
  if (/^[\d#*\s]+$/.test(t)) return false; // digits are "emoji components" too
  const count = typeof Intl !== 'undefined' && Intl.Segmenter
    ? [...new Intl.Segmenter(undefined, { granularity: 'grapheme' }).segment(t.replace(/\s+/g, ''))].length
    : [...t.replace(/\s+/g, '')].length;
  return count <= 3;
}
