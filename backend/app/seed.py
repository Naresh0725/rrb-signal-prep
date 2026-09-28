"""Original educational seed items. No real-paper or verified-PYQ claims.
Numerical items are deterministic and include worked calculations.
"""

import random, json
from sqlalchemy import select
from .db import Question, Config, Topic

ROWS = []


def add(
    subject,
    topic,
    text,
    answer,
    wrong,
    explanation,
    i=0,
    subtopic="",
    concept=None,
    formula=None,
    given=None,
    calculation=None,
    final_answer=None,
):
    # Structured fields are backfilled only where the caller supplies them
    # (numeric templates with a clear derivation); every other seed question
    # keeps working unchanged with just the plain `explanation` text.
    opts = [str(answer)] + [str(v) for v in wrong]
    assert len(set(opts)) == 4, (text, opts)
    random.Random(text).shuffle(opts)
    ROWS.append(
        dict(
            id=f"seed-{len(ROWS)+1:04d}",
            question_text=text,
            option_a=opts[0],
            option_b=opts[1],
            option_c=opts[2],
            option_d=opts[3],
            correct_option="ABCD"[opts.index(str(answer))],
            explanation=explanation,
            concept=concept,
            formula=formula,
            given=given,
            calculation=calculation,
            final_answer=final_answer,
            subject=subject,
            topic=topic,
            subtopic=subtopic or topic,
            difficulty=[
                "Easy",
                "Medium",
                "Medium",
                "Hard",
                "Easy",
                "Medium",
                "Hard",
                "Medium",
                "Easy",
                "Medium",
            ][i % 10],
            source_type="ORIGINAL",
            source_reference="SignalPrep original educational seed; not a previous-year question.",
            verification_status="REVIEWED",
            generation_method="deterministic-seed",
            status="ACTIVE",
        )
    )


for i in range(15):
    r = 10 + i * 2
    v = r * 3
    add(
        "Science & Engineering",
        "Network Theory",
        f"A {r} Ω resistor is connected across a {v} V DC supply. What is the power dissipated?",
        f"{r*9} W",
        [f"{r*3} W", f"{r*6} W", f"{r*12} W"],
        f"Using P = V²/R: {v}²/{r} = {r*9} W. The current is {v}/{r} = 3 A.",
        i,
        "Resistive power",
        concept="Power dissipated in a resistor connected across a DC supply is found from the voltage and resistance.",
        formula="P = V² / R",
        given=f"V = {v} V\nR = {r} Ω",
        calculation=f"P = V² / R\nP = {v}² / {r}\nP = {v*v} / {r}\nP = {r*9} W",
        final_answer=f"{r*9} W",
    )
    turns = 100 + i * 20
    sec = turns * 2
    add(
        "Science & Engineering",
        "Transformers",
        f"An ideal transformer has {turns} primary turns and {sec} secondary turns. The secondary supplies {i+2} A. What is the primary current?",
        f"{(i+2)*2} A",
        [f"{i+2} A", f"{(i+2)/2:g} A", f"{(i+2)*4} A"],
        f"For an ideal transformer, Ip/Is = Ns/Np = 2. Thus Ip = 2 × {i+2} = {(i+2)*2} A.",
        i + 2,
        "Current ratio",
        concept="In an ideal transformer, primary and secondary current are inversely proportional to the turns ratio.",
        formula="Ip / Is = Ns / Np",
        given=f"Np = {turns}\nNs = {sec}\nIs = {i+2} A",
        calculation=f"Ip / Is = Ns / Np = {sec}/{turns} = 2\nIp = 2 × Is = 2 × {i+2} = {(i+2)*2} A",
        final_answer=f"{(i+2)*2} A",
    )
    a = i + 2
    b = i + 3
    add(
        "Science & Engineering",
        "Measurements",
        f"A sensor produces {a} mV per °C. Its output changes by {a*b} mV. What temperature change does this represent?",
        f"{b} °C",
        [f"{b+1} °C", f"{b+2} °C", f"{b+3} °C"],
        f"Temperature change = output change / sensitivity = {a*b}/{a} = {b} °C.",
        i + 3,
        "Sensitivity",
        concept="A linear sensor's output change is the sensitivity multiplied by the change in the measured quantity.",
        formula="ΔT = output change / sensitivity",
        given=f"Sensitivity = {a} mV/°C\nOutput change = {a*b} mV",
        calculation=f"ΔT = {a*b} / {a}\nΔT = {b} °C",
        final_answer=f"{b} °C",
    )
    freq = 100 * (i + 1)
    add(
        "Science & Engineering",
        "Communication Systems",
        f"A baseband signal contains frequencies up to {freq} Hz. What is its theoretical Nyquist sampling rate?",
        f"{freq*2} samples/s",
        [f"{freq} samples/s", f"{freq//2} samples/s", f"{freq*4} samples/s"],
        f"The Nyquist rate is twice the highest frequency: 2 × {freq} = {freq*2} samples/s. Practical sampling generally uses a higher rate.",
        i + 4,
        "Sampling",
        concept="The Nyquist sampling theorem says a signal must be sampled at least twice its highest frequency to avoid aliasing.",
        formula="Nyquist rate = 2 × highest frequency",
        given=f"Highest frequency = {freq} Hz",
        calculation=f"Nyquist rate = 2 × {freq}\nNyquist rate = {freq*2} samples/s",
        final_answer=f"{freq*2} samples/s",
    )
for i in range(10):
    p = 1000 + 200 * i
    t = 2 + i % 3
    add(
        "Mathematics",
        "Simple Interest",
        f"Find the simple interest on ₹{p} at 5% per year for {t} years.",
        f"₹{p*t//20}",
        [f"₹{p*t//10}", f"₹{p*t//20+50}", f"₹{p*t//20-50}"],
        f"Simple interest = PRT/100 = {p} × 5 × {t}/100 = ₹{p*t//20}.",
        i,
        concept="Simple interest grows linearly with the principal, rate and time.",
        formula="SI = P × R × T / 100",
        given=f"P = ₹{p}\nR = 5% per year\nT = {t} years",
        calculation=f"SI = {p} × 5 × {t} / 100\nSI = {p*5*t} / 100\nSI = ₹{p*t//20}",
        final_answer=f"₹{p*t//20}",
    )
    a = 10 + i
    add(
        "Mathematics",
        "Averages",
        f"The mean of {a} observations is 12. Adding one observation of 25 gives what new mean?",
        f"{(12*a+25)/(a+1):.2f}",
        ["12.00", "25.00", "18.50"],
        f"Total becomes 12 × {a} + 25 = {12*a+25}. Divide by {a+1}: {(12*a+25)/(a+1):.2f}, rounded to two decimals.",
        i + 1,
        concept="A new mean after adding one observation equals the new total divided by the new count.",
        formula="New mean = (old mean × old count + new observation) / new count",
        given=f"Old mean = 12\nOld count = {a}\nNew observation = 25",
        calculation=f"Total = 12 × {a} + 25 = {12*a+25}\nNew mean = {12*a+25} / {a+1} = {(12*a+25)/(a+1):.2f}",
        final_answer=f"{(12*a+25)/(a+1):.2f}",
    )
    speed = 30 + 6 * i
    add(
        "Mathematics",
        "Speed & Distance",
        f"A train travels at {speed} km/h for 20 minutes at constant speed. How far does it travel?",
        f"{speed//3} km",
        [f"{speed} km", f"{speed//3*2} km", f"{speed*3} km"],
        f"20 minutes = 1/3 hour. Distance = {speed} × 1/3 = {speed//3} km.",
        i + 2,
        concept="Distance travelled at constant speed equals speed multiplied by time, with time converted to hours.",
        formula="Distance = Speed × Time",
        given=f"Speed = {speed} km/h\nTime = 20 minutes = 1/3 hour",
        calculation=f"Distance = {speed} × 1/3\nDistance = {speed//3} km",
        final_answer=f"{speed//3} km",
    )
    x = 5 + i
    add(
        "Mathematics",
        "Algebra",
        f"If 3x + 7 = {3*x+7}, find x.",
        str(x),
        [str(x + 1), str(x - 1), str(x + 3)],
        f"Subtract 7 and divide by 3: x = ({3*x+7} − 7)/3 = {x}.",
        i + 3,
        concept="Solve a linear equation by isolating x: undo addition, then undo multiplication.",
        formula="x = (RHS − 7) / 3",
        given=f"3x + 7 = {3*x+7}",
        calculation=f"3x = {3*x+7} − 7\n3x = {3*x}\nx = {3*x} / 3\nx = {x}",
        final_answer=str(x),
    )
for i in range(10):
    a = 3 + i
    d = 4 + i
    add(
        "Reasoning",
        "Number Series",
        f"Find the next term: {a}, {a+d}, {a+2*d}, {a+3*d}, …",
        a + 4 * d,
        [a + 5 * d, a + 3 * d + 1, a + 4 * d - 1],
        f"The difference is consistently +{d}. The next term is {a+3*d} + {d} = {a+4*d}.",
        i,
        concept="In an arithmetic series each term increases by the same constant difference.",
        formula="Next term = last term + common difference",
        given=f"Series: {a}, {a+d}, {a+2*d}, {a+3*d}\nCommon difference = {d}",
        calculation=f"Next term = {a+3*d} + {d}\nNext term = {a+4*d}",
        final_answer=str(a + 4 * d),
    )
    east = 3 * (i + 1)
    north = 4 * (i + 1)
    add(
        "Reasoning",
        "Directions",
        f"A person walks {east} m east and then {north} m north. What is the straight-line distance from the starting point?",
        f"{5*(i+1)} m",
        [f"{east+north} m", f"{north-east} m", f"{2*(east+north)} m"],
        f"Use Pythagoras: √({east}² + {north}²) = {5*(i+1)} m.",
        i + 2,
        concept="Two perpendicular movements form a right triangle; the straight-line distance is the hypotenuse.",
        formula="Distance = √(east² + north²)",
        given=f"East = {east} m\nNorth = {north} m",
        calculation=f"Distance = √({east}² + {north}²)\nDistance = √({east*east} + {north*north})\nDistance = √{east*east+north*north}\nDistance = {5*(i+1)} m",
        final_answer=f"{5*(i+1)} m",
    )
    n = 20 + i * 2
    rank = 4 + i
    add(
        "Reasoning",
        "Ranking",
        f"In a line of {n} people, Arun is {rank}th from the front. What is his position from the back?",
        n - rank + 1,
        [n - rank, n - rank + 2, rank],
        f"Position from back = total − position from front + 1 = {n} − {rank} + 1 = {n-rank+1}.",
        i + 3,
        concept="Position from the back of a line relates to position from the front through the total count.",
        formula="Position from back = Total − Position from front + 1",
        given=f"Total people = {n}\nPosition from front = {rank}",
        calculation=f"Position from back = {n} − {rank} + 1\nPosition from back = {n-rank+1}",
        final_answer=str(n - rank + 1),
    )
computer_facts = [
    (
        "Hardware",
        "Which component executes machine instructions?",
        "CPU",
        ["Monitor", "Keyboard", "Printer"],
        "The central processing unit fetches, decodes and executes machine instructions.",
    ),
    (
        "Memory",
        "Which memory normally loses its contents when power is removed?",
        "RAM",
        ["ROM", "SSD", "Optical disc"],
        "Ordinary RAM is volatile memory; it requires power to retain stored data.",
    ),
    (
        "Networking",
        "Which protocol resolves a domain name to an IP address?",
        "DNS",
        ["FTP", "SMTP", "IMAP"],
        "The Domain Name System resolves domain names to resource records including IP addresses.",
    ),
    (
        "Networking",
        "Which device forwards packets between different IP networks?",
        "Router",
        ["Repeater", "Hub", "Keyboard"],
        "A router uses a routing table to forward packets between IP networks.",
    ),
    (
        "Security",
        "Which attack attempts to obtain credentials using deceptive messages?",
        "Phishing",
        ["Defragmentation", "Compression", "Indexing"],
        "Phishing impersonates trusted sources to trick a user into disclosing sensitive information.",
    ),
    (
        "Operating Systems",
        "What is the main role of an operating system scheduler?",
        "Allocate CPU time to tasks",
        ["Draw spreadsheet charts", "Encrypt every file", "Translate domain names"],
        "The scheduler decides which runnable task receives CPU time.",
    ),
    (
        "Databases",
        "Which SQL clause filters rows before grouping?",
        "WHERE",
        ["HAVING", "ORDER BY", "GROUP BY"],
        "WHERE filters individual rows before aggregate grouping. HAVING filters groups.",
    ),
    (
        "Databases",
        "What uniquely identifies each row in a relational table?",
        "Primary key",
        ["Display width", "View name", "Comment"],
        "A primary key uniquely identifies rows and cannot contain null key values.",
    ),
    (
        "Software",
        "A compiler primarily performs which task?",
        "Translates source code",
        ["Supplies electrical power", "Routes network packets", "Scans printed pages"],
        "A compiler translates source code into another representation, commonly executable machine code.",
    ),
    (
        "Memory",
        "What is the main purpose of a CPU cache?",
        "Reduce average memory-access latency",
        [
            "Increase screen resolution",
            "Store paper documents",
            "Replace all permanent storage",
        ],
        "A cache keeps frequently or recently used data close to the CPU for faster access.",
    ),
    (
        "Networking",
        "Which protocol is used for reliable, ordered transport of a byte stream?",
        "TCP",
        ["UDP", "ARP", "ICMP"],
        "TCP provides a reliable, ordered byte stream using acknowledgements and retransmission.",
    ),
    (
        "Security",
        "Which property does a cryptographic hash primarily help check?",
        "Data integrity",
        ["Screen brightness", "Battery health", "Network cable length"],
        "Comparing a trusted hash with a computed hash helps detect changes to data.",
    ),
    (
        "Operating Systems",
        "What is a deadlock?",
        "Tasks waiting indefinitely for each other’s resources",
        ["A normal shutdown", "A successful backup", "An empty queue"],
        "Deadlock occurs when tasks cannot proceed because each waits on resources held by others in a cycle.",
    ),
    (
        "Databases",
        "Which normal form removes repeating groups and requires atomic column values?",
        "First normal form",
        ["Second normal form", "Third normal form", "Boyce–Codd normal form"],
        "First normal form requires atomic column values and eliminates repeating groups.",
    ),
    (
        "Hardware",
        "Which device converts a printed page into digital image data?",
        "Scanner",
        ["Speaker", "Projector", "Plotter"],
        "A scanner is an input device that captures printed material as digital images.",
    ),
    (
        "Software",
        "What is an algorithm?",
        "A finite sequence of well-defined steps",
        [
            "Only a programming language",
            "A physical storage device",
            "An internet address",
        ],
        "An algorithm specifies a finite, well-defined procedure for solving a problem.",
    ),
    (
        "Networking",
        "What does an IPv4 address contain?",
        "32 bits",
        ["16 bits", "64 bits", "128 bits"],
        "An IPv4 address consists of 32 bits, usually written as four decimal octets.",
    ),
    (
        "Security",
        "Which is an example of two-factor authentication?",
        "Password and authenticator code",
        ["Password entered twice", "Two usernames", "Two security questions"],
        "A password is a knowledge factor and an authenticator device provides a possession factor.",
    ),
    (
        "Databases",
        "Which SQL keyword eliminates duplicate result rows?",
        "DISTINCT",
        ["JOIN", "UPDATE", "INSERT"],
        "SELECT DISTINCT returns unique combinations of the selected columns.",
    ),
    (
        "Operating Systems",
        "Virtual memory allows a process to use what?",
        "A logical address space mapped to physical storage",
        ["Unlimited actual RAM", "Only CPU registers", "A physical keyboard buffer"],
        "Virtual memory maps process virtual addresses to physical memory and, when supported, backing storage.",
    ),
]
for i, (topic, text, a, w, e) in enumerate(computer_facts):
    add("Computers", topic, text, a, w, e, i)
for i in range(10):
    n = i + 5
    add(
        "Computers",
        "Number Systems",
        f"What is the binary representation of decimal {n}?",
        bin(n)[2:],
        [bin(n + 1)[2:], bin(n + 2)[2:], bin(n - 1)[2:]],
        f"Decimal {n} equals binary {bin(n)[2:]}; each binary digit represents a power of two.",
        i,
    )
    kb = i + 2
    add(
        "Computers",
        "Memory",
        f"Using 1 KiB = 1,024 bytes, how many bytes are in {kb} KiB?",
        kb * 1024,
        [kb * 1000, kb * 1024 + 1024, kb * 512],
        f"{kb} × 1,024 = {kb*1024} bytes. KiB is the binary unit kibibyte.",
        i + 3,
    )
ga = [
    (
        "Indian Polity",
        "On which date did the Constitution of India come into force?",
        "26 January 1950",
        ["15 August 1947", "26 November 1949", "2 October 1950"],
        "The Constitution was adopted on 26 November 1949 and came into force on 26 January 1950.",
    ),
    (
        "Geography",
        "Which is the largest ocean on Earth?",
        "Pacific Ocean",
        ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean"],
        "The Pacific Ocean has the largest surface area of the world’s oceans.",
    ),
    (
        "General Science",
        "What is the SI unit of force?",
        "Newton",
        ["Joule", "Watt", "Pascal"],
        "Force is measured in newtons; one newton equals one kg·m/s².",
    ),
    (
        "History",
        "Who wrote the Indian national anthem Jana Gana Mana?",
        "Rabindranath Tagore",
        ["Bankim Chandra Chattopadhyay", "Sarojini Naidu", "Subramania Bharati"],
        "Rabindranath Tagore composed Jana Gana Mana.",
    ),
    (
        "Geography",
        "Which latitude is approximately 23.5° north?",
        "Tropic of Cancer",
        ["Tropic of Capricorn", "Equator", "Antarctic Circle"],
        "The Tropic of Cancer lies approximately 23.5 degrees north of the equator.",
    ),
    (
        "Indian Polity",
        "Fundamental Rights are primarily contained in which part of the Indian Constitution?",
        "Part III",
        ["Part I", "Part IV", "Part V"],
        "Part III of the Indian Constitution contains the Fundamental Rights.",
    ),
    (
        "General Science",
        "Which gas is most abundant in Earth’s dry atmosphere?",
        "Nitrogen",
        ["Oxygen", "Carbon dioxide", "Hydrogen"],
        "Nitrogen makes up approximately 78% of Earth’s dry atmosphere by volume.",
    ),
    (
        "History",
        "The Dandi March of 1930 protested which colonial tax?",
        "Salt tax",
        ["Land revenue only", "Income tax", "Import tax on tea"],
        "Gandhi’s Dandi March challenged the British salt monopoly and salt tax.",
    ),
    (
        "Geography",
        "Which layer lies directly below Earth’s crust?",
        "Mantle",
        ["Inner core", "Outer core", "Ionosphere"],
        "The mantle lies below the crust and above the outer core.",
    ),
    (
        "General Science",
        "What is the chemical symbol for sodium?",
        "Na",
        ["S", "So", "Sn"],
        "The chemical symbol Na comes from the Latin name natrium.",
    ),
    (
        "Economics",
        "What does inflation describe?",
        "A sustained rise in the general price level",
        [
            "A fall in all wages",
            "An increase only in exports",
            "A decline in population",
        ],
        "Inflation describes a sustained rise in the overall price level, reducing money’s purchasing power.",
    ),
    (
        "Indian Polity",
        "Which house of Parliament is also called the Council of States?",
        "Rajya Sabha",
        ["Lok Sabha", "Vidhan Sabha", "Gram Sabha"],
        "Rajya Sabha is the Council of States; Lok Sabha is the House of the People.",
    ),
    (
        "General Science",
        "Which organ pumps blood through the human circulatory system?",
        "Heart",
        ["Liver", "Kidney", "Lung"],
        "The heart is the muscular pump that circulates blood through the body.",
    ),
    (
        "Geography",
        "The Equator divides Earth into which hemispheres?",
        "Northern and Southern",
        ["Eastern and Western", "Arctic and Antarctic", "Land and Water"],
        "The Equator is latitude zero and divides Earth into northern and southern hemispheres.",
    ),
    (
        "History",
        "Who is commonly credited with discovering penicillin in 1928?",
        "Alexander Fleming",
        ["Louis Pasteur", "Edward Jenner", "Robert Koch"],
        "Alexander Fleming observed the antibacterial action of Penicillium mould in 1928.",
    ),
    (
        "General Science",
        "What is the SI unit of electric current?",
        "Ampere",
        ["Volt", "Ohm", "Coulomb"],
        "Electric current is measured in amperes; a coulomb measures electric charge.",
    ),
    (
        "Indian Polity",
        "Directive Principles of State Policy are in which part of the Indian Constitution?",
        "Part IV",
        ["Part II", "Part III", "Part VI"],
        "The Directive Principles of State Policy are set out in Part IV.",
    ),
    (
        "Geography",
        "Which planet is known for its prominent ring system?",
        "Saturn",
        ["Mercury", "Venus", "Mars"],
        "Saturn has an extensive and highly visible ring system made largely of ice particles.",
    ),
    (
        "General Science",
        "What is the pH of pure water at 25°C approximately?",
        "7",
        ["1", "10", "14"],
        "Pure water is neutral at 25°C, with pH approximately 7.",
    ),
    (
        "Economics",
        "What is the opportunity cost of a choice?",
        "Value of the next best alternative forgone",
        ["All historical spending", "Only its cash price", "The total national income"],
        "Opportunity cost is the benefit of the best alternative given up when making a choice.",
    ),
]
for i, (topic, text, a, w, e) in enumerate(ga):
    add("General Awareness", topic, text, a, w, e, i)


def seed(s):
    from .preparation import seed_preparation

    seed_preparation(s)
    if not s.get(Config, "exam-prep"):
        s.add(
            Config(
                id="exam-prep",
                name="Exam preparation · verified PYQs + hard patterns",
                distribution={
                    "Science & Engineering": 35,
                    "Computers": 20,
                    "Mathematics": 20,
                    "Reasoning": 15,
                    "General Awareness": 10,
                },
                duration_minutes=90,
                source_mix={"PYQ": 50, "PYQ_PATTERN": 50},
                difficulty_mix={"Hard": 100},
                cooldown_days=365,
            )
        )
    legacy = s.get(Config, "grade1")
    if legacy and legacy.name == "Grade-I Signal · Full Mock":
        legacy.name = "Basic concepts · 100 questions"

    if not s.get(Config, "grade1"):
        s.add(
            Config(
                id="grade1",
                name="Basic concepts · 100 questions",
                distribution={
                    "Science & Engineering": 35,
                    "Computers": 20,
                    "Mathematics": 20,
                    "Reasoning": 15,
                    "General Awareness": 10,
                },
                duration_minutes=90,
                source_mix={"ORIGINAL": 100},
                difficulty_mix={"Easy": 30, "Medium": 50, "Hard": 20},
                cooldown_days=7,
            )
        )
    if not s.get(Config, "quick"):
        s.add(
            Config(
                id="quick",
                name="Quick Practice · 10 Questions",
                distribution={
                    "Science & Engineering": 4,
                    "Computers": 2,
                    "Mathematics": 2,
                    "Reasoning": 1,
                    "General Awareness": 1,
                },
                duration_minutes=10,
                source_mix={"ORIGINAL": 100},
                difficulty_mix={"Easy": 30, "Medium": 50, "Hard": 20},
                cooldown_days=7,
            )
        )
    for row in ROWS:
        if s.get(Question, row["id"]):
            continue
        topic = s.scalar(
            select(Topic).where(
                Topic.subject == row["subject"], Topic.name == row["topic"]
            )
        )
        if not topic:
            topic = Topic(subject=row["subject"], name=row["topic"])
            s.add(topic)
            s.flush()
        s.add(
            Question(
                **row,
                topic_id=topic.id,
                generation_metadata={
                    "seed": True,
                    "note": "Educational seed; review against your exam syllabus. Difficulty is an initial editorial label, not empirically calibrated.",
                },
            )
        )


if __name__ == "__main__":
    from .db import Base, engine, Session

    Base.metadata.create_all(engine)
    with Session() as s:
        seed(s)
        s.commit()
    print(f"Seeded {len(ROWS)} original questions.")
