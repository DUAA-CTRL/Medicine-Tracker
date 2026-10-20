import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date, time
import json


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Medicine Buddy",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_NAME = "medicine_buddy.db"


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def column_exists(conn, table_name, column_name):
    rows = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(
        row["name"] == column_name
        for row in rows
    )


def add_column_if_missing(
    conn,
    table,
    column,
    definition
):
    if not column_exists(
        conn,
        table,
        column
    ):
        conn.execute(
            f"ALTER TABLE {table} "
            f"ADD COLUMN {column} {definition}"
        )


def init_database():

    conn = get_db()

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password TEXT,
            role TEXT DEFAULT 'member',
            active INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)

    add_column_if_missing(
        conn,
        "users",
        "password",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "users",
        "role",
        "TEXT DEFAULT 'member'"
    )

    add_column_if_missing(
        conn,
        "users",
        "active",
        "INTEGER DEFAULT 1"
    )

    add_column_if_missing(
        conn,
        "users",
        "created_at",
        "TEXT"
    )

    # --------------------------------------------------------
    # MEDICINES
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            medicine_name TEXT NOT NULL,
            dose TEXT DEFAULT '',
            frequency TEXT DEFAULT '',
            timings TEXT DEFAULT '',
            reminder_time TEXT DEFAULT '',
            start_date TEXT,
            end_date TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT
        )
    """)

    add_column_if_missing(
        conn,
        "medicines",
        "dose",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "medicines",
        "frequency",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "medicines",
        "timings",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "medicines",
        "reminder_time",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "medicines",
        "start_date",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "medicines",
        "end_date",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "medicines",
        "notes",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "medicines",
        "created_at",
        "TEXT"
    )

    # --------------------------------------------------------
    # DOSES
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS doses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            dose_date TEXT NOT NULL,
            timing TEXT NOT NULL,
            status TEXT NOT NULL,
            updated_at TEXT
        )
    """)

    # FIX FOR:
    # sqlite3.OperationalError:
    # table doses has no column named updated_at

    add_column_if_missing(
        conn,
        "doses",
        "updated_at",
        "TEXT"
    )

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    admin = conn.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        ("Duaa",)
    ).fetchone()

    if admin is None:

        conn.execute(
            """
            INSERT INTO users
            (
                username,
                name,
                password,
                role,
                active,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Duaa",
                "Duaa Zahir",
                hash_password("admin123"),
                "admin",
                1,
                datetime.now().isoformat(),
            )
        )

    else:

        conn.execute(
            """
            UPDATE users
            SET name = ?,
                role = ?,
                active = 1
            WHERE username = ?
            """,
            (
                "Duaa Zahir",
                "admin",
                "Duaa",
            )
        )

        if not admin["password"]:

            conn.execute(
                """
                UPDATE users
                SET password = ?
                WHERE username = ?
                """,
                (
                    hash_password("admin123"),
                    "Duaa",
                )
            )

    conn.commit()
    conn.close()


init_database()


# ============================================================
# SESSION
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "remember_me" not in st.session_state:
    st.session_state.remember_me = False


# ============================================================
# THEME
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #f7f4ec;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #876612 !important;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #eadfbd;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 4px 16px rgba(100, 75, 20, .07);
    }

    [data-testid="stMetricValue"] {
        color: #9b7412 !important;
    }

    input,
    textarea {
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] > div {
        border-radius: 10px !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        background: #b58a22 !important;
        color: white !important;
        border: 0 !important;
        border-radius: 11px !important;
        min-height: 44px;
        font-weight: 700;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: #8d6912 !important;
        color: white !important;
    }

    .login-box {
        background: white;
        border: 1px solid #eadfbd;
        border-radius: 24px;
        padding: 30px;
        box-shadow: 0 10px 35px rgba(80,60,20,.10);
    }

    .gold-text {
        color: #9b7412;
        font-weight: 800;
    }

    .small-muted {
        color: #77705f;
        font-size: 14px;
    }

    .medicine-card {
        background: white;
        border: 1px solid #eadfbd;
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 5px 18px rgba(80,60,20,.07);
    }

    @media (max-width: 768px) {

        .block-container {
            padding: 10px 10px 35px 10px;
        }

        .login-box {
            padding: 20px;
            border-radius: 18px;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            min-height: 48px;
        }

        input,
        textarea {
            font-size: 16px !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# AUTH
# ============================================================

def authenticate(username, password):

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        AND active = 1
        """,
        (username.strip(),)
    ).fetchone()

    conn.close()

    if user is None:
        return None

    if not user["password"]:
        return None

    if user["password"] == hash_password(password):
        return user

    return None


def update_password(user_id, new_password):

    conn = get_db()

    conn.execute(
        """
        UPDATE users
        SET password = ?
        WHERE id = ?
        """,
        (
            hash_password(new_password),
            user_id,
        )
    )

    conn.commit()
    conn.close()


# ============================================================
# DOSE FUNCTIONS
# ============================================================

def get_dose_status(
    medicine_id,
    dose_date,
    timing
):

    conn = get_db()

    row = conn.execute(
        """
        SELECT status
        FROM doses
        WHERE medicine_id = ?
        AND dose_date = ?
        AND timing = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            medicine_id,
            dose_date,
            timing,
        )
    ).fetchone()

    conn.close()

    if row:
        return row["status"]

    return None


def save_dose(
    medicine_id,
    dose_date,
    timing,
    status
):

    conn = get_db()

    existing = conn.execute(
        """
        SELECT id
        FROM doses
        WHERE medicine_id = ?
        AND dose_date = ?
        AND timing = ?
        """,
        (
            medicine_id,
            dose_date,
            timing,
        )
    ).fetchone()

    now = datetime.now().isoformat()

    if existing:

        conn.execute(
            """
            UPDATE doses
            SET status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                now,
                existing["id"],
            )
        )

    else:

        conn.execute(
            """
            INSERT INTO doses
            (
                medicine_id,
                dose_date,
                timing,
                status,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                medicine_id,
                dose_date,
                timing,
                status,
                now,
            )
        )

    conn.commit()
    conn.close()


# ============================================================
# LOGIN
# ============================================================

if not st.session_state.logged_in:

    left, center, right = st.columns(
        [1, 2, 1]
    )

    with center:

        st.markdown(
            '<div class="login-box">',
            unsafe_allow_html=True
        )

        st.title("💊 Medicine Buddy")

        st.caption(
            "Your personal medicine companion"
        )

        st.divider()

        st.subheader("🔐 Secure Login")

        st.write(
            "Welcome back! Please login to continue."
        )

        username = st.text_input(
            "Username",
            placeholder="Enter username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        remember = st.checkbox(
            "Remember password on this device"
        )

        login = st.button(
            "🔐 LOGIN",
            use_container_width=True
        )

        if login:

            if not username.strip():

                st.error(
                    "Please enter username."
                )

            elif not password:

                st.error(
                    "Please enter password."
                )

            else:

                logged_user = authenticate(
                    username,
                    password
                )

                if logged_user:

                    st.session_state.user = dict(
                        logged_user
                    )

                    st.session_state.logged_in = True
                    st.session_state.remember_me = remember

                    st.success(
                        f"Welcome, {logged_user['name']} 💛"
                    )

                    st.rerun()

                else:

                    st.error(
                        "❌ Invalid username or password."
                    )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    st.stop()


# ============================================================
# CURRENT USER
# ============================================================

user = st.session_state.user

user_id = user["id"]
user_name = user["name"]
username = user["username"]
role = user["role"]

is_admin = role == "admin"


# ============================================================
# HEADER
# ============================================================

header1, header2 = st.columns(
    [4, 1]
)

with header1:

    st.title("💊 Medicine Buddy")

    st.caption(
        f"Welcome, {user_name} 💛"
    )

with header2:

    if st.button(
        "Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.user = None

        st.rerun()


# ============================================================
# ADMIN PANEL
# ============================================================

if is_admin:

    st.success(
        "👑 Admin Panel • Duaa Zahir"
    )

    admin_tabs = st.tabs(
        [
            "📊 Dashboard",
            "👥 Members",
            "💊 Medicines",
            "🔐 Account",
        ]
    )

    # ========================================================
    # DASHBOARD
    # ========================================================

    with admin_tabs[0]:

        conn = get_db()

        members_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role = 'member'
            AND active = 1
            """
        ).fetchone()[0]

        medicines_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM medicines
            """
        ).fetchone()[0]

        taken_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM doses
            WHERE status = 'Taken'
            """
        ).fetchone()[0]

        missed_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM doses
            WHERE status = 'Missed'
            """
        ).fetchone()[0]

        skipped_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM doses
            WHERE status = 'Skipped'
            """
        ).fetchone()[0]

        conn.close()

        a, b, c, d, e = st.columns(5)

        a.metric("👥 Members", members_count)
        b.metric("💊 Medicines", medicines_count)
        c.metric("✅ Taken", taken_count)
        d.metric("❌ Missed", missed_count)
        e.metric("⏭️ Skipped", skipped_count)

        st.divider()

        st.subheader("📋 Recent Medicine Assignments")

        conn = get_db()

        rows = conn.execute(
            """
            SELECT
                medicines.*,
                users.name AS member_name
            FROM medicines
            LEFT JOIN users
            ON medicines.user_id = users.id
            ORDER BY medicines.id DESC
            """
        ).fetchall()

        conn.close()

        if not rows:
            st.info("No medicines assigned yet.")

        for med in rows:

            with st.container(border=True):

                st.subheader(
                    f"💊 {med['medicine_name']}"
                )

                st.write(
                    f"👤 **Member:** {med['member_name']}"
                )

                st.write(
                    f"💉 **Dose:** {med['dose']}"
                )

                st.write(
                    f"🔄 **Frequency:** {med['frequency']}"
                )

                st.write(
                    f"⏰ **Timing:** {med['timings']}"
                )


    # ========================================================
    # MEMBERS
    # ========================================================

    with admin_tabs[1]:

        st.subheader("➕ Add Member")

        with st.form("add_member"):

            member_name = st.text_input(
                "Member Name",
                placeholder="Example: Ali"
            )

            member_username = st.text_input(
                "Username",
                placeholder="Example: ali123"
            )

            member_password = st.text_input(
                "Password",
                type="password",
                placeholder="Minimum 6 characters"
            )

            add = st.form_submit_button(
                "➕ ADD MEMBER",
                use_container_width=True
            )

        if add:

            if not member_name.strip():
                st.error("Member name is required.")

            elif not member_username.strip():
                st.error("Username is required.")

            elif len(member_password) < 6:
                st.error(
                    "Password must contain at least 6 characters."
                )

            else:

                conn = get_db()

                try:

                    conn.execute(
                        """
                        INSERT INTO users
                        (
                            username,
                            name,
                            password,
                            role,
                            active,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            member_username.strip(),
                            member_name.strip(),
                            hash_password(member_password),
                            "member",
                            1,
                            datetime.now().isoformat()
                        )
                    )

                    conn.commit()

                    st.success(
                        f"🎉 {member_name} added successfully!"
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        "❌ Username already exists."
                    )

                finally:

                    conn.close()

        st.divider()

        conn = get_db()

        members = conn.execute(
            """
            SELECT *
            FROM users
            WHERE role = 'member'
            AND active = 1
            ORDER BY name
            """
        ).fetchall()

        conn.close()

        st.subheader("👥 Members")

        if not members:

            st.info("No members yet.")

        else:

            for member in members:

                with st.container(border=True):

                    st.write(
                        f"### 👤 {member['name']}"
                    )

                    st.caption(
                        f"Username: @{member['username']}"
                    )

            options = {
                f"{m['name']} (@{m['username']})":
                m["id"]
                for m in members
            }

            st.divider()

            # PASSWORD RESET

            st.subheader("🔑 Reset Member Password")

            reset_choice = st.selectbox(
                "Select member",
                list(options.keys()),
                key="reset_choice"
            )

            reset_password = st.text_input(
                "New Password",
                type="password",
                key="reset_password"
            )

            if st.button(
                "🔑 RESET PASSWORD",
                use_container_width=True
            ):

                if len(reset_password) < 6:

                    st.error(
                        "Password must contain at least 6 characters."
                    )

                else:

                    update_password(
                        options[reset_choice],
                        reset_password
                    )

                    st.success(
                        "✅ Password reset successfully."
                    )

            st.divider()

            # DELETE

            st.subheader("🗑️ Delete Member")

            delete_choice = st.selectbox(
                "Select member to delete",
                list(options.keys()),
                key="delete_choice"
            )

            confirm_delete = st.checkbox(
                "I confirm that I want to delete this member and their medicine records."
            )

            if st.button(
                "🗑️ DELETE MEMBER",
                use_container_width=True
            ):

                if not confirm_delete:

                    st.warning(
                        "Please confirm deletion."
                    )

                else:

                    delete_id = options[
                        delete_choice
                    ]

                    conn = get_db()

                    medicine_rows = conn.execute(
                        """
                        SELECT id
                        FROM medicines
                        WHERE user_id = ?
                        """,
                        (delete_id,)
                    ).fetchall()

                    for med in medicine_rows:

                        conn.execute(
                            """
                            DELETE FROM doses
                            WHERE medicine_id = ?
                            """,
                            (med["id"],)
                        )

                    conn.execute(
                        """
                        DELETE FROM medicines
                        WHERE user_id = ?
                        """,
                        (delete_id,)
                    )

                    conn.execute(
                        """
                        DELETE FROM users
                        WHERE id = ?
                        AND role = 'member'
                        """,
                        (delete_id,)
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        "✅ Member deleted."
                    )

                    st.rerun()


    # ========================================================
    # MEDICINES
    # ========================================================

    with admin_tabs[2]:

        st.subheader(
            "💊 Assign Medicine"
        )

        conn = get_db()

        members = conn.execute(
            """
            SELECT id, name, username
            FROM users
            WHERE role = 'member'
            AND active = 1
            ORDER BY name
            """
        ).fetchall()

        conn.close()

        if not members:

            st.warning(
                "Please create a member first."
            )

        else:

            member_options = {
                f"{m['name']} (@{m['username']})":
                m["id"]
                for m in members
            }

            selected = st.selectbox(
                "👤 Select Member",
                list(member_options.keys())
            )

            with st.form(
                "medicine_form"
            ):

                medicine_name = st.text_input(
                    "Medicine Name",
                    placeholder="Example: Paracetamol"
                )

                dose = st.text_input(
                    "Dose",
                    placeholder="Example: 1 tablet"
                )

                frequency = st.selectbox(
                    "Frequency",
                    [
                        "Once daily",
                        "Twice daily",
                        "Three times daily",
                        "Four times daily",
                        "As needed"
                    ]
                )

                timings = st.multiselect(
                    "⏰ Medicine Timing",
                    [
                        "Morning",
                        "Afternoon",
                        "Evening",
                        "Night"
                    ]
                )

                reminder_time = st.time_input(
                    "⏰ Reminder Time",
                    value=time(8, 0)
                )

                start_date = st.date_input(
                    "Start Date",
                    value=date.today()
                )

                end_date = st.date_input(
                    "End Date",
                    value=date.today()
                )

                notes = st.text_area(
                    "Instructions",
                    placeholder="Example: Take after food."
                )

                assign = st.form_submit_button(
                    "💊 ASSIGN MEDICINE",
                    use_container_width=True
                )

            if assign:

                if not medicine_name.strip():

                    st.error(
                        "Medicine name is required."
                    )

                elif not dose.strip():

                    st.error(
                        "Dose is required."
                    )

                elif not timings:

                    st.error(
                        "Please select timing."
                    )

                elif end_date < start_date:

                    st.error(
                        "End date cannot be before start date."
                    )

                else:

                    timing_text = ", ".join(
                        timings
                    )

                    conn = get_db()

                    conn.execute(
                        """
                        INSERT INTO medicines
                        (
                            user_id,
                            medicine_name,
                            dose,
                            frequency,
                            timings,
                            reminder_time,
                            start_date,
                            end_date,
                            notes,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            member_options[selected],
                            medicine_name.strip(),
                            dose.strip(),
                            frequency,
                            timing_text,
                            reminder_time.strftime(
                                "%I:%M %p"
                            ),
                            str(start_date),
                            str(end_date),
                            notes.strip(),
                            datetime.now().isoformat()
                        )
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        f"💊 Medicine assigned to "
                        f"{selected.split(' (@')[0]}!"
                    )

                    st.rerun()

        st.divider()

        st.subheader(
            "📋 All Medicines"
        )

        conn = get_db()

        medicines = conn.execute(
            """
            SELECT
                medicines.*,
                users.name AS member_name
            FROM medicines
            LEFT JOIN users
            ON medicines.user_id = users.id
            ORDER BY medicines.id DESC
            """
        ).fetchall()

        conn.close()

        for med in medicines:

            with st.container(border=True):

                st.subheader(
                    f"💊 {med['medicine_name']}"
                )

                st.write(
                    f"👤 **Member:** {med['member_name']}"
                )

                st.write(
                    f"💉 **Dose:** {med['dose']}"
                )

                st.write(
                    f"🔄 **Frequency:** {med['frequency']}"
                )

                st.write(
                    f"⏰ **Timing:** {med['timings']}"
                )

                if med["reminder_time"]:

                    st.write(
                        f"🔔 **Reminder:** "
                        f"{med['reminder_time']}"
                    )

                st.write(
                    f"📅 **Course:** "
                    f"{med['start_date']} → "
                    f"{med['end_date']}"
                )

                if med["notes"]:

                    st.info(
                        f"📝 {med['notes']}"
                    )


    # ========================================================
    # ADMIN ACCOUNT
    # ========================================================

    with admin_tabs[3]:

        st.subheader(
            "👑 Duaa Zahir"
        )

        st.write(
            "Username: **Duaa**"
        )

        st.divider()

        st.subheader(
            "🔐 Change Admin Password"
        )

        current = st.text_input(
            "Current Password",
            type="password"
        )

        new_admin = st.text_input(
            "New Password",
            type="password"
        )

        confirm_admin = st.text_input(
            "Confirm Password",
            type="password"
        )

        if st.button(
            "🔐 CHANGE PASSWORD",
            use_container_width=True
        ):

            if not authenticate(
                "Duaa",
                current
            ):

                st.error(
                    "❌ Current password is incorrect."
                )

            elif len(new_admin) < 6:

                st.error(
                    "Password must contain at least 6 characters."
                )

            elif new_admin != confirm_admin:

                st.error(
                    "Passwords do not match."
                )

            else:

                update_password(
                    user_id,
                    new_admin
                )

                st.success(
                    "✅ Admin password changed."
                )


# ============================================================
# MEMBER PANEL
# ============================================================

else:

    current_hour = datetime.now().hour

    if current_hour < 12:
        greeting = f"Good morning, {user_name}! 🌅"

    elif current_hour < 17:
        greeting = f"Good afternoon, {user_name}! ☀️"

    elif current_hour < 21:
        greeting = f"Good evening, {user_name}! 🌆"

    else:
        greeting = f"Good night, {user_name}! 🌙"

    st.success(greeting)

    st.write(
        f"Here is your medicine dashboard, "
        f"**{user_name}**. 💛"
    )

    member_tabs = st.tabs(
        [
            "💊 My Medicines",
            "📅 History",
            "⚙️ Account"
        ]
    )

    # ========================================================
    # MY MEDICINES
    # ========================================================

    with member_tabs[0]:

        st.subheader(
            f"💊 {user_name}'s Medicines"
        )

        conn = get_db()

        medicines = conn.execute(
            """
            SELECT *
            FROM medicines
            WHERE user_id = ?
            ORDER BY end_date
            """,
            (user_id,)
        ).fetchall()

        conn.close()

        if not medicines:

            st.info(
                f"No medicine has been assigned "
                f"to {user_name} yet."
            )

        for med in medicines:

            with st.container(border=True):

                st.subheader(
                    f"💊 {med['medicine_name']}"
                )

                st.write(
                    f"👤 **For:** {user_name}"
                )

                st.write(
                    f"💉 **Dose:** {med['dose']}"
                )

                st.write(
                    f"🔄 **Frequency:** {med['frequency']}"
                )

                st.write(
                    f"⏰ **Timing:** {med['timings']}"
                )

                if med["reminder_time"]:

                    st.write(
                        f"🔔 **Reminder:** "
                        f"{med['reminder_time']}"
                    )

                st.write(
                    f"📅 **Course:** "
                    f"{med['start_date']} → "
                    f"{med['end_date']}"
                )

                if med["notes"]:

                    st.info(
                        f"📝 {med['notes']}"
                    )

                st.divider()

                timing_list = [
                    x.strip()
                    for x in med["timings"].split(",")
                    if x.strip()
                ]

                for timing_name in timing_list:

                    status = get_dose_status(
                        med["id"],
                        str(date.today()),
                        timing_name
                    )

                    st.write(
                        f"### ⏰ {timing_name}"
                    )

                    if status == "Taken":

                        st.success(
                            f"🎉 Amazing {user_name}! "
                            f"You took your {timing_name.lower()} "
                            f"medicine. 💚"
                        )

                    elif status == "Missed":

                        st.error(
                            f"❌ {user_name}, your "
                            f"{timing_name.lower()} dose "
                            f"was marked as missed."
                        )

                    elif status == "Skipped":

                        st.warning(
                            f"⏭️ {user_name}, you skipped "
                            f"your {timing_name.lower()} dose."
                        )

                    else:

                        st.info(
                            f"💛 Hey {user_name}! "
                            f"It's time to take your "
                            f"{timing_name.lower()} medicine."
                        )

                        x, y, z = st.columns(3)

                        with x:

                            if st.button(
                                "✅ Taken",
                                key=f"taken_{med['id']}_{timing_name}",
                                use_container_width=True
                            ):

                                save_dose(
                                    med["id"],
                                    str(date.today()),
                                    timing_name,
                                    "Taken"
                                )

                                st.balloons()

                                st.success(
                                    f"🎉 Well done, {user_name}! "
                                    f"You took your medicine. "
                                    f"Keep taking care of yourself! 💛"
                                )

                                st.rerun()

                        with y:

                            if st.button(
                                "❌ Missed",
                                key=f"missed_{med['id']}_{timing_name}",
                                use_container_width=True
                            ):

                                save_dose(
                                    med["id"],
                                    str(date.today()),
                                    timing_name,
                                    "Missed"
                                )

                                st.error(
                                    f"❌ Okay {user_name}. "
                                    f"This dose has been marked missed."
                                )

                                st.rerun()

                        with z:

                            if st.button(
                                "⏭️ Skip",
                                key=f"skip_{med['id']}_{timing_name}",
                                use_container_width=True
                            ):

                                save_dose(
                                    med["id"],
                                    str(date.today()),
                                    timing_name,
                                    "Skipped"
                                )

                                st.warning(
                                    f"⏭️ {user_name}, "
                                    f"this dose has been skipped."
                                )

                                st.rerun()

                st.divider()


    # ========================================================
    # HISTORY
    # ========================================================

    with member_tabs[1]:

        st.subheader(
            f"📅 {user_name}'s Medicine History"
        )

        conn = get_db()

        history = conn.execute(
            """
            SELECT
                doses.dose_date,
                doses.timing,
                doses.status,
                medicines.medicine_name,
                medicines.dose
            FROM doses
            JOIN medicines
            ON doses.medicine_id = medicines.id
            WHERE medicines.user_id = ?
            ORDER BY
                doses.dose_date DESC,
                doses.id DESC
            """,
            (user_id,)
        ).fetchall()

        conn.close()

        if not history:

            st.info(
                "No medicine history yet."
            )

        for item in history:

            text = (
                f"{item['dose_date']} • "
                f"{item['medicine_name']} • "
                f"{item['dose']} • "
                f"{item['timing']}"
            )

            if item["status"] == "Taken":

                st.success(
                    f"✅ {text} — Taken"
                )

            elif item["status"] == "Missed":

                st.error(
                    f"❌ {text} — Missed"
                )

            else:

                st.warning(
                    f"⏭️ {text} — Skipped"
                )


    # ========================================================
    # MEMBER ACCOUNT
    # ========================================================

    with member_tabs[2]:

        st.subheader(
            f"👤 {user_name}"
        )

        st.write(
            f"Username: **@{username}**"
        )

        st.divider()

        st.subheader(
            "🔐 Change Password"
        )

        old_password = st.text_input(
            "Current Password",
            type="password",
            key="old_pass"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            key="new_pass"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            key="confirm_pass"
        )

        if st.button(
            "🔐 CHANGE PASSWORD",
            use_container_width=True
        ):

            if not authenticate(
                username,
                old_password
            ):

                st.error(
                    "❌ Current password is incorrect."
                )

            elif len(new_password) < 6:

                st.error(
                    "Password must contain at least 6 characters."
                )

            elif new_password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                update_password(
                    user_id,
                    new_password
                )

                st.success(
                    "✅ Password changed successfully."
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "💊 Medicine Buddy • Take care of yourself 💛"
)