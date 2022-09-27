from .themes import THEME
import math


def make_echo(level_state):
    # Can echo flag.
    if level_state.level_gen_flags & 2 != 0:
        if level_state.prng.level_gen.next_chance(100) < 4:
            level_state.level_width = 6
            level_state.level_height = 6
            level_state.is_echo_level = True


def flag_liquid_rooms(level_state):
    flag_liquid_rooms_wh(level_state, level_state.level_width, level_state.level_height)


def flag_liquid_rooms_wh(level_state, width, height):
    count = width * height
    possible_rooms = [i for i in range(count)]

    for _ in range(
        min(
            count,
            level_state.level_chances.flagged_liquid_rooms,
        )
    ):
        index = level_state.prng.level_gen.next_chance(count)
        room = possible_rooms[index]
        possible_rooms.remove(room)
        count -= 1
        level_state.rooms_meta[math.floor(room / width)][
            room % width
        ].flagged_liquid = True


def generate_path(level_state, theme, retry):
    if retry:
        for x in range(8):
            for y in range(15):
                level_state.rooms_f[y][x] = 0
        level_state.rooms_f[level_state.spawn_room_y][level_state.spawn_room_x] = 5
    room_x = level_state.spawn_room_x
    room_y = level_state.spawn_room_y
    past_room_y = room_y
    new_room_y = room_y
    new_room_x = room_x

    exit_y_level = theme.exit_y_level(level_state)
    directionbool = room_y < exit_y_level
    directionbit = directionbool and 1 or 0
    direction = directionbool and 1 or -1

    # -1=left,1=right,0=down
    move_direction = None
    while True:
        new_room_x = room_x
        room_y = new_room_y
        if room_x == 0:
            chance = level_state.prng.level_gen.next_chance(3)
            if chance == 2:
                move_direction = 0
            elif room_x < level_state.level_width - 1:
                move_direction = 1
            else:
                move_direction = 0
        else:
            rightedge = room_x == level_state.level_width - 1
            chance = level_state.prng.level_gen.next_chance((rightedge and 0 or 2) + 3)
            chance += rightedge and 2 or -2
            if chance >= 0 and chance < 3:
                if chance < 2:
                    move_direction = 1
                else:
                    move_direction = 0
            else:
                move_direction = -1

        if move_direction == 0:
            new_room_y = room_y + direction
            # We have moved past the exit layer, make an exit and end the loop.
            if (
                exit_y_level != new_room_y
                and (new_room_y <= exit_y_level) != directionbool
            ):
                # Exit or exit notop depending on where the path came from.
                level_state.rooms_f[room_y][room_x] = 0x8 - (
                    room_y == past_room_y and 1 or 0
                )
                return
            previous_room = level_state.rooms_f[room_y][room_x]
            # Make entrance into entrance_drop.
            if previous_room == 0x5:
                previous_room = 0x6
            else:
                if previous_room == (directionbit | 2):
                    # Turns path-drops going up (SC) and path-notops going down into path-drop-notop.
                    previous_room = 0x4
                else:
                    # Turns path-normal into path-drop when going down and path-notop when going up.
                    previous_room = 0x3 ^ directionbit

            level_state.rooms_f[room_y][room_x] = previous_room

            # New room becomes a path-notop when going down or a path-drop when going up.
            level_state.rooms_f[new_room_y][new_room_x] = directionbit | 2
            room_x = new_room_x
        else:
            new_room_x = room_x + move_direction
            if level_state.rooms_f[new_room_y][new_room_x] != 0:
                new_room_x = room_x
            new_room_y = room_y
            room_x = new_room_x

        past_room_y = room_y
        if level_state.rooms_f[new_room_y][new_room_x] == 0:
            level_state.rooms_f[new_room_y][new_room_x] = 1

def set_backlayer_related(level_state, room_code, is_hard, bool4, layer, x, y):

def set_backlayer_room(level_state, x, y, room_code):


class ThemeInfo:
    def __init__(
        self,
    ):
        self.should_attempt_bee_spawn = False
        self.unknown2 = False

    def load_level_file(self, level_state):
        level_state.level_width = 4
        level_state.level_height = 4
        level_state.altar_chance = 14

    def init_flags(self, level_state):
        pass

    def init_level(self, level_state):
        pass

    def has_looping_borders(self, level_state):
        return False

    def flag_liquid_rooms(self, level_state):
        flag_liquid_rooms(level_state)

    def generate_path(self, level_state, retry):
        generate_path(level_state, self, retry)

    def exit_y_level(self, level_state):
        return level_state.level_height - 1

    def add_special_rooms(self, level_state):
        pass


class Dwelling(ThemeInfo):
    def init_flags(self, level_state):
        level_state.level_gen_flags &= 0xFFF7FF

    def init_level(self, level_state):
        run_state = level_state.run_state
        if level_state.level == 4:
            # Clear can_echo and 2 other unknown flags.
            level_state.level_gen_flags &= 0xFEBFFD
            # Ghist shop
            level_state.backlayer_shop_type = 0xC
        else:
            if level_state.level == 1:
                level_state.level_gen_flags &= 0xFBFFF9
            # No shop has spawned.
            if run_state.quest_flags & 0x10 == 0:
                # Pick one of the 4 base shop types.
                level_state.shop_type = (level_state.prng.level_gen.next() >> 0x1E) & 3
            make_echo(level_state)
            level_state.spawn_room_x = level_state.prng.level_gen.next_chance(
                level_state.level_width
            )
            level_state.spawn_room_y = 0
            level_state.rooms_f[0][level_state.spawn_room_x] = 5

            # 1-2 or 1-3 and no udjat has spawned.
            if level_state.level & 0xFE == 2 and run_state.quest_flags & 0x10000 == 0:
                udjat = (
                    level_state.prng.level_gen.next_chance(4 - level_state.level) + 1
                )
                if level_state.level > 2:
                    udjat = 4 - level_state.level
                if udjat == 1:
                    run_state.presence_flags = 1
                    # Cannot be dark.
                    run_state.level_flags &= 0xFFFDFFFF

    def add_special_rooms(self, level_state):
        run_state = level_state.run_state
        if level_state.level == 4:
            # Caveboss
            for x in range(level_state.level_width):
                for y in range(level_state.level_height):
                    if level_state.rooms_f[y][x] != 0x19:
                        level_state.rooms_f[y][x] = 1
                        level_state.rooms_meta[y][x].setroom_f = True
            level_state.rooms_f[0][2] = 5
            level_state.rooms_f[2][1] = 0x16
            level_state.rooms_f[2][2] = 0x16
            level_state.rooms_f[2][3] = 0x16
            level_state.rooms_f[3][2] = 0x57
            level_state.rooms_f[4][0] = 7
            level_state.rooms_f[4][2] = 0x16
            level_state.rooms_f[4][4] = 7
        elif run_state.presence_flags == 1:
            # Udjat Level
            primary_positions = []
            secondary_positions = []
            for x in range(level_state.level_width):
                for y in range(level_state.level_height):
                    if level_state.rooms_f[y][x] == 1:
                        secondary_positions.append(y * 8 + x)
                    elif level_state.rooms_f[y][x] == 0:
                        primary_positions.append(y * 8 + x)
            positions = (
                len(primary_positions) > 0 and primary_positions or secondary_positions
            )
            position = positions[level_state.prng.level_gen.next_chance(len(positions))]

            x = position % 8
            y = math.floor(position / 8)
            level_state.rooms_f[y][x] = 0x1D
            level_state.rooms_b[y][x] = 0x1D
            level_state.rooms_b[y - 1][x] = 0x1E
            level_state.presence_flags = 0


class Jungle(ThemeInfo):
    def init_level(self, level_state):
        run_state = level_state.run_state
        # 2-2, 2-3, 2-4, and BM has not spawned.
        if level_state.level > 1 and run_state.quest_flags & 0x20000 == 0:
            bm = level_state.prng.level_gen.next_chance(5 - level_state.level) + 1
            if bm == 1:
                level_state.level_height = 8
                run_state.presence_flags = 2
                level_state.level_gen_flags &= 0xFBFFFD

        # Moon challenge
        if (
            run_state.presence_flags != 2
            and level_state.level > 1
            and run_state.quest_flags & 0x1000000 == 0
        ):
            run_state.presence_flags = 0x100
        make_echo(level_state)
        level_state.spawn_room_x = level_state.prng.level_gen.next_chance(
            level_state.level_width
        )
        level_state.spawn_room_y = 0
        level_state.rooms_f[0][level_state.spawn_room_x] = 5

    def flag_liquid_rooms(self, level_state):
        flag_liquid_rooms(level_state)
        if level_state.theme != THEME.COSMIC_OCEAN:
            self.should_attempt_bee_spawn = True
        self.unknown2 = True

    def exit_y_level(self, level_state):
        # Black Market
        if level_state.run_state.presence_flags == 2:
            return 3
        return level_state.level_height - 1

    def generate_path(self, level_state, retry):
        super().generate_path(level_state, False)

        if (level_state.run_state.presence_flags != 2 and level_state.level == 4) or (
            level_state.level == 3
            and level_state.quest_flags & 0x40000 == 0  # This a bug?
        ):
            # Keep generating path until there is room for special rooms.
            while True:
                for x in range(level_state.level_width):
                    if level_state.rooms_f[0][x] == 0 or level_state.rooms_f[1][x] == 0:
                        return
                super().generate_path(level_state, True)

    def add_special_rooms(self, level_state):
        run_state = level_state.run_state
        if run_state.presence_flags == 2:
            # BM
            if level_state.level_height > 5:
                for y in range(4, level_state.level_height - 1):
                    for x in range(level_state.level_width):
                        # Filled room
                        level_state.rooms_f[y][x] = 0x15
            if level_state.level_height > 4:
                for y in range(4, level_state.level_height):
                    for x in range(level_state.level_width):
                        # Filled room
                        level_state.rooms_b[y][x] = 0x77


class Volcana(ThemeInfo):
    def init_level(self, level_state):
        run_state = level_state.run_state
        # 2-2, 2-3, 2-4, and Drill has not spawned.
        if level_state.level > 1 and run_state.quest_flags & 0x40000 == 0:
            drill = level_state.prng.level_gen.next_chance(5 - level_state.level) + 1
            if drill == 1:
                level_state.level_height = 7
                run_state.presence_flags = 4
                # Stop ghost jar from spawning.
                run_state.level_flags |= 0x40
                # Spawn entrance at and edge room.
                level_state.spawn_room_x = (level_state.level_width - 1) * (
                    (level_state.prng.level_gen.next() >> 0x1F) & 1
                )
                level_state.spawn_room_y = 0
                level_state.rooms_f[0][level_state.spawn_room_x] = 5
                return
        # Moon challenge
        if level_state.level > 1 and run_state.quest_flags & 0x1000000 == 0:
            run_state.presence_flags = 0x100
        make_echo(level_state)
        level_state.spawn_room_x = level_state.prng.level_gen.next_chance(
            level_state.level_width
        )
        level_state.spawn_room_y = 0
        level_state.rooms_f[0][level_state.spawn_room_x] = 5

    def flag_liquid_rooms(self, level_state):
        # Drill or echo or CO
        if (
            level_state.run_state.presence_flags == 4
            or (level_state.level_width == 6 and level_state.level_height == 6)
            or level_state.theme == THEME.COSMIC_OCEAN
        ):
            level_state.level_chances.max_liquid_paticles = 900
        flag_liquid_rooms_wh(level_state, 4, 4)

        # Drill
        if level_state.run_state.presence_flags == 4:
            b = (level_state.prng.level_gen.next() >> 0x1E) & 2
            a = (b >> 1) + 1
            print("a: ", a)
            print("b: ", b)
            level_state.rooms_f[0][a] = 0x78
        self.unknown2 = True

    def exit_y_level(self, level_state):
        # Drill
        if level_state.run_state.presence_flags == 4:
            return 3
        return level_state.level_height - 1

    def generate_path(self, level_state, retry):
        super().generate_path(level_state, False)

        if (level_state.run_state.presence_flags != 4 and level_state.level == 4) or (
            level_state.level == 3
            and level_state.quest_flags & 0x20000 == 0  # This a bug?
        ):
            # Keep generating path until there is room for special rooms.
            while True:
                for x in range(level_state.level_width):
                    if level_state.rooms_f[0][x] == 0 or level_state.rooms_f[1][x] == 0:
                        return
                super().generate_path(level_state, True)

    def add_special_rooms(self, level_state):
        run_state = level_state.run_state
        if run_state.presence_flags == 4:
            # Drill
            if level_state.level_height > 4:
                for y in range(4, level_state.level_height):
                    for x in range(level_state.level_width):
                        # Filled room
                        level_state.rooms_f[y][x] = 0x15
                for x in range(level_state.level_width):
                    level_state.rooms_f[level_state.level_height - 1][x] = 0x7A
                # Make bottom layer exit on opposite side center of drill.
                level_state.rooms_f[level_state.level_height - 1][
                    level_state.rooms_f[0][1] == 0x78 and 2 or 1
                ] = 7
                level_state.rooms_f[level_state.level_height - 1][
                    (level_state.prng.level_gen.next() & 0x80000000 == 0)
                    and 0
                    or (level_state.level_width - 1)
                ] = 0x79


class Olmec(ThemeInfo):
    def init_level(self, level_state):
        run_state = level_state.run_state
        run_state.level_flags &= 0xFDFFFF
        level_state.level_width = 5
        level_state.level_height = 8
        level_state.spawn_room_x = 0
        level_state.spawn_room_y = 1
        level_state.level_gen_flags &= 0x173FDE


class TidePool(ThemeInfo):
    def init_flags(self, level_state):
        level_state.level_gen_flags &= 0xFFF7FF

    def init_level(self, level_state):
        run_state = level_state.run_state
        if level_state.level & 2 == 2:
            level_state.level_gen_flags &= 0xFFFFFD
            level_state.level_height = 6
        if level_state.level == 2:
            run_state.presence_flags = 0x200
        make_echo(level_state)
        level_state.spawn_room_x = level_state.prng.level_gen.next_chance(
            level_state.level_width
        )
        level_state.spawn_room_y = 0
        level_state.rooms_f[0][level_state.spawn_room_x] = 5

    def flag_liquid_rooms(self, level_state):
        flag_liquid_rooms(level_state)
        self.unknown2 = True

    def exit_y_level(self, level_state):
        # 4-2 and 4-3
        if level_state.level & 0xFE == 2:
            return 3
        return level_state.level_height - 1

    def generate_path(self, level_state, retry):
        super().generate_path(level_state, False)

        if level_state.run_state.presence_flags == 0x200:
            # Keep generating path until there is room for special rooms.
            while True:
                if (
                    level_state.rooms_f[1][1] == 0
                    or level_state.rooms_f[1][2] == 0
                    or level_state.rooms_f[2][1] == 0
                    or level_state.rooms_f[2][2] == 0
                ):
                    return
                super().generate_path(level_state, True)


class Temple(ThemeInfo):
    def init_flags(self, level_state):
        level_state.level_gen_flags &= 0xFFFDFF
        if not self.has_looping_borders(level_state):
            level_state.locust_plague = (
                level_state.prng.level_gen.next_chance(1000) == 0
            )

    def init_level(self, level_state):
        run_state = level_state.run_state
        if level_state.level == 2:
            run_state.presence_flags = 0x200
            level_state.level_gen_flags &= 0xFFFFFD
        make_echo(level_state)
        level_state.spawn_room_x = level_state.prng.level_gen.next_chance(
            level_state.level_width
        )
        level_state.spawn_room_y = 0
        level_state.rooms_f[0][level_state.spawn_room_x] = 5
        if level_state.level_width > 4 or level_state.level_height > 4:
            level_state.locust_plague = False

    def flag_liquid_rooms(self, level_state):
        flag_liquid_rooms(level_state)
        if level_state.theme != THEME.COSMIC_OCEAN:
            self.should_attempt_bee_spawn = True
        self.unknown2 = True

    def generate_path(self, level_state, retry):
        super().generate_path(level_state, False)

        if level_state.run_state.presence_flags == 0x200:
            # Keep generating path until there is room for special rooms.
            while True:
                if (
                    level_state.rooms_f[1][1] == 0
                    or level_state.rooms_f[1][2] == 0
                    or level_state.rooms_f[2][1] == 0
                    or level_state.rooms_f[2][2] == 0
                    or level_state.rooms_f[3][1] == 0
                    or level_state.rooms_f[3][2] == 0
                ):
                    return
                super().generate_path(level_state, True)


class IceCaves(ThemeInfo):
    def __init(self):
        super().__init__()
        self.cave_height = 4

    def init_level(self, level_state):
        run_state = level_state.run_state
        level_state.is_dark_level = False
        run_state.level_flags &= 0xFFFDFFFF
        level_state.level_gen_flags &= 0xFFDFF9
        make_echo(level_state)
        level_state.spawn_room_x = level_state.prng.level_gen.next_chance(
            level_state.level_width
        )
        level_state.spawn_room_y = 0
        level_state.rooms_f[0][level_state.spawn_room_x] = 5
        # [theme_info + 0x10] = level_state.level_height???
        self.cave_height = level_state.level_height

    def exit_y_level(self, level_state):
        return self.cave_height - 1


class NeoBabylon(ThemeInfo):
    def init_level(self, level_state):
        # No Dead are Restless
        level_state.level_gen_flags &= 0xFFFFFB
        if level_state.level == 2:
            # Cannot echo
            level_state.level_gen_flags &= 0xFFDFFD
        elif level_state.level == 1:
            level_state.level_gen_flags &= 0xFBFFFF
            level_state.level_chances.altar_chance = 0
        elif level_state.level == 3:  # And not killed Tusk.
            level_state.level_height = 5
            level_state.level_gen_flags &= 0xFDDFFD
        make_echo(level_state)
        level_state.spawn_room_x = level_state.prng.level_gen.next_chance(
            level_state.level_width
        )
        level_state.spawn_room_y = 0
        level_state.rooms_f[0][level_state.spawn_room_x] = 5


class SunkenCity(ThemeInfo):
    def load_level_file(self, level_state):
        super().load_level_file(level_state)
        level_state.level_height = 5

    def init_flags(self, level_state):
        level_state.level_gen_flags &= 0xFFFCF9
        if level_state.level == 1:
            level_state.level_gen_flags = 0xFFF8FF

    def init_level(self, level_state):
        make_echo(level_state)
        level_state.spawn_room_x = level_state.prng.level_gen.next_chance(
            level_state.level_width
        )
        level_state.spawn_room_y = level_state.level_height - 1
        level_state.rooms_f[level_state.spawn_room_y][level_state.spawn_room_x] = 5
        if level_state.quest_flags & 0x04000000 == 0:
            level_state.run_state.presence_flags = 0x400

    def exit_y_level(self, level_state):
        return 0

    def generate_path(self, level_state, retry):
        super().generate_path(level_state, False)

        if level_state.run_state.presence_flags == 0x400 and level_state.level == 3:
            # Keep generating path until there is room for special rooms.
            while True:
                if (
                    level_state.rooms_f[1][1] == 0
                    or level_state.rooms_f[1][2] == 0
                    or level_state.rooms_f[2][1] == 0
                    or level_state.rooms_f[2][2] == 0
                    or level_state.rooms_f[3][1] == 0
                    or level_state.rooms_f[3][2] == 0
                    or level_state.rooms_f[4][1] == 0
                    or level_state.rooms_f[4][2] == 0
                ):
                    return
                super().generate_path(level_state, True)


class CosmicOcean(ThemeInfo):
    def __init__(self):
        super().__init__()
        self.subtheme = None

    def load_level_file(self, level_state):
        super().load_level_file(level_state)
        subtheme_index = (level_state.prng.level_gen.next() >> 0x1D) & 7
        if subtheme_index == 0:
            self.subtheme = Dwelling()
        if subtheme_index == 1:
            self.subtheme = Jungle()
        if subtheme_index == 2:
            self.subtheme = Volcana()
        if subtheme_index == 3:
            self.subtheme = TidePool()
        if subtheme_index == 4:
            self.subtheme = Temple()
        if subtheme_index == 5:
            self.subtheme = IceCaves()
        if subtheme_index == 6:
            self.subtheme = NeoBabylon()
        if subtheme_index == 7:
            self.subtheme = SunkenCity()

    def init_flags(self, level_state):
        if self.subtheme:
            self.subtheme.init_flags(level_state)

    def init_level(self, level_state):
        run_state = level_state.run_state
        level_state.level_width = ((level_state.prng.level_gen.next() >> 0x1E) & 3) + 5
        level_state.level_height = level_state.prng.level_gen.next_chance(5) + 4

        level_state.spawn_room_x = (
            level_state.prng.level_gen.next_chance(level_state.level_width - 2) + 1
        )
        level_state.spawn_room_y = (
            level_state.prng.level_gen.next_chance(level_state.level_height - 2) + 1
        )
        level_state.rooms_f[level_state.spawn_room_y][level_state.spawn_room_x] = 5

        exit_x = level_state.spawn_room_x
        exit_y = level_state.spawn_room_y
        while exit_x == level_state.spawn_room_x and exit_y == level_state.spawn_room_y:
            exit_x = (
                level_state.prng.level_gen.next_chance(level_state.level_width - 2) + 1
            )
            exit_y = (
                level_state.prng.level_gen.next_chance(level_state.level_height - 2) + 1
            )
        level_state.rooms_f[exit_y][exit_x] = 7
        # Cannot be dark.
        run_state.level_flags &= 0xFFFDFFFF
        level_state.is_dark_level = False
        # Stop pet from spawning.
        run_state.level_flags |= 0x8
        level_state.level_gen_flags &= 0xC04FEC
        lvl = level_state.level
        if not (lvl == 10 or lvl == 50 or lvl == 90):
            # No player coffins.
            level_state.level_gen_flags &= 0xFFFFCC

    def flag_liquid_rooms(self, level_state):
        if self.subtheme:
            self.subtheme.flag_liquid_rooms(level_state)


class CityOfGold(ThemeInfo):
    def init_level(self, level_state):
        run_state = level_state.run_state
        # Cannot echo
        level_state.level_gen_flags &= 0xFFFFFD
        make_echo(level_state)
        level_state.spawn_room_x = level_state.prng.level_gen.next_chance(
            level_state.level_width
        )
        level_state.spawn_room_y = 0
        level_state.rooms_f[0][level_state.spawn_room_x] = 5
        # Cannot be dark.
        run_state.level_flags &= 0xFFFDFFFF
        level_state.is_dark_level = False
        level_state.level_gen_flags &= 0xF9CFFF


class Duat(ThemeInfo):
    def init_level(self, level_state):
        run_state = level_state.run_state

        level_state.spawn_room_x = (
            level_state.prng.level_gen.next_chance(level_state.level_width - 2) + 1
        )
        level_state.spawn_room_y = 9
        level_state.rooms_f[level_state.spawn_room_y][level_state.spawn_room_x] = 5

        # Cannot be dark.
        run_state.level_flags &= 0xFFFDFFFF
        level_state.is_dark_level = False
        # Stop pet from spawning.
        run_state.level_flags |= 0x8

        level_state.level_gen_flags &= 0x016BFE

    def exit_y_level(self, level_state):
        return 2


class Abzu(ThemeInfo):
    def init_level(self, level_state):
        run_state = level_state.run_state

        level_state.spawn_room_x = 3
        level_state.spawn_room_y = 3

        # Cannot be dark.
        run_state.level_flags &= 0xFFFDFFFF
        level_state.is_dark_level = False

        level_state.level_gen_flags &= 0xF05FFE


class Tiamat(ThemeInfo):
    def init_level(self, level_state):
        run_state = level_state.run_state
        r = level_state.prng.level_gen.next_int()
        exit_x = (r >> 0x1E) & 2
        level_state.spawn_room_x = exit_x ^ 2
        level_state.spawn_room_y = 8
        level_state.rooms_f[level_state.spawn_room_y][level_state.spawn_room_x] = 5
        level_state.rooms_f[level_state.spawn_room_y][exit_x] = 7
        if r & 0x80000000 == 1:  # ????????
            level_state.rooms_meta[8][0].flipped = True
            level_state.rooms_meta[8][2].flipped = True

        # Cannot be dark.
        run_state.level_flags &= 0xFFFDFFFF
        level_state.is_dark_level = False

        level_state.level_gen_flags &= 0xF07FDE


class EggplantWorld(ThemeInfo):
    def load_level_file(self, level_state):
        super().load_level_file(level_state)
        level_state.level_height = 8

    def init_level(self, level_state):
        run_state = level_state.run_state
        level_state.level_gen_flags &= 0xF15DF2

        # Cannot be dark.
        run_state.level_flags &= 0xFFFDFFFF
        level_state.is_dark_level = False
        # Ghist shop
        level_state.backlayer_shop_type = 0xC

        level_state.spawn_room_x = level_state.prng.level_gen.next_chance(
            level_state.level_width
        )
        level_state.spawn_room_y = level_state.level_height - 1
        level_state.rooms_f[level_state.spawn_room_y][level_state.spawn_room_x] = 5

    def exit_y_level(self, level_state):
        return 0


class Hundun(ThemeInfo):
    def load_level_file(self, level_state):
        super().load_level_file(level_state)
        level_state.level_width = 3
        level_state.level_height = 12

    def init_level(self, level_state):
        run_state = level_state.run_state

        level_state.spawn_room_x = 0
        level_state.spawn_room_y = 9
        level_state.rooms_f[level_state.spawn_room_y][level_state.spawn_room_x] = 5

        # Cannot be dark.
        run_state.level_flags &= 0xFFFDFFFF
        level_state.is_dark_level = False
        # Stop pet from spawning.
        run_state.level_flags |= 0x8

        level_state.level_gen_flags &= 0xF15DDE

    def exit_y_level(self, level_state):
        return 1


def theme_info_for_theme(theme):
    if theme == THEME.DWELLING:
        return Dwelling()
    elif theme == THEME.JUNGLE:
        return Jungle()
    elif theme == THEME.VOLCANA:
        return Volcana()
    elif theme == THEME.OLMEC:
        return Olmec()
    elif theme == THEME.TIDE_POOL:
        return TidePool()
    elif theme == THEME.TEMPLE:
        return Temple()
    elif theme == THEME.ICE_CAVES:
        return IceCaves()
    elif theme == THEME.NEO_BABYLON:
        return NeoBabylon()
    elif theme == THEME.SUNKEN_CITY:
        return SunkenCity()
    elif theme == THEME.COSMIC_OCEAN:
        return CosmicOcean()
    elif theme == THEME.CITY_OF_GOLD:
        return CityOfGold()
    elif theme == THEME.DUAT:
        return Duat()
    elif theme == THEME.ABZU:
        return Abzu()
    elif theme == THEME.TIAMAT:
        return Tiamat()
    elif theme == THEME.EGGPLANT_WORLD:
        return Tiamat()
    elif theme == THEME.HUNDUN:
        return Tiamat()
    return ThemeInfo()


def initialize_run_state(level_state):
    run_state = level_state.run_state
    run_state.ushabti = level_state.prng.tables[2].next_chance(100)


def generate_level(level_state):
    theme_info = theme_info_for_theme(level_state.theme)
    theme_info.load_level_file(level_state)

    run_state = level_state.run_state
    if level_state.level + level_state.world == 2:
        initialize_run_state(level_state)

    run_state.presence_flags = 0
    run_state.level_flags &= 0xFE000007
    run_state.level_flags |= 0x00080000
    if level_state.level == 1:
        # Clear the dark and vault spawned in world flags.
        run_state.quest_flags &= 0xFFFFFFF9

    # Skip if dark level has spawned in world.
    if run_state.quest_flags & 2 == 0:
        # Skip on 1-1
        if level_state.world + level_state.level != 2:
            if level_state.prng.level_gen.next_chance(12) == 0:
                level_state.is_dark_level = True
                run_state.level_flags |= 0x20000
                run_state.quest_flags |= 0x2

    run_state.shop_type = level_state.prng.level_gen.next_chance(7)
    # 9 = Tun, 10 = Caveman
    run_state.backlayer_shop_type = 10 - (
        level_state.prng.level_gen.next_chance(100) < 79
    )

    theme_info.init_flags(level_state)
    theme_info.init_level(level_state)
    theme_info.flag_liquid_rooms(level_state)
    # Remember, this flag is backwards
    if level_state.level_gen_flags & 0x10000 != 0:
        theme_info.generate_path(level_state, False)

    theme_info.add_special_rooms(level_state)
