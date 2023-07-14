
import nextcord
from nextcord.ext import commands, menus
from bingo import discordbingo, commands, tiles, bingodata, teams, board




class TileSelect(nextcord.ui.Select):

    def selectableTiles(self, tileSet):
        """Selectable tiles are non-xp tiles, and tile sets that contain at least one non-xp tile"""

        ret = []

        for sl, t in tileSet.subtiles.items():
            if isinstance(t, tiles.TileSet):
                subtiles = self.selectableTiles(t)
                if subtiles:
                    ret.append((sl, t))
            elif not isinstance(t, tiles.XPTile):
                ret.append((sl, t))

        return ret

    def __init__(self, tileSet):
        options = []

        for sl, t in self.selectableTiles(tileSet):
            options.append(nextcord.SelectOption(label=t.name, description=t.description, value=sl))

        super().__init__(
            placeholder="Select Tile",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: nextcord.Interaction):
        await self.view.tileSelected(self.values[0])


class TileSelectView(nextcord.ui.View):
    def __init__(self, tileSet):
        super().__init__()

        self.add_item(TileSelect(tileSet))
        self.tile = None

    async def tileSelected(self, value):
        self.tile = value
        self.stop()



class TileBasicApproveView(nextcord.ui.View):
    """Confirmation buttons to approve a tile"""

    def __init__(self):
        super().__init__()
        self.value = None

    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.value = True
        self.stop()

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.value = False
        self.stop()


class TileCountApproveView(nextcord.ui.View):
    """buttons to add an amount to a tile, for example laps of a rooftop

    Discord is very limited by how to achieve this, best approach we've seen is to have a button
    that sets the amount to add, then plus and minus buttons. """

    def __init__(self, message):
        super().__init__()
        self.value = 0
        self.multiplier = 0
        self.multipliers = [1, 5, 10, 50, 100]
        self.baseText = message

    @nextcord.ui.button(label="x1", style=nextcord.ButtonStyle.grey)
    async def multiplierSet(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.multiplier = (self.multiplier + 1) % len(self.multipliers)
        button.label = f"x{self.multipliers[self.multiplier]}"

        await interaction.response.edit_message(view=self)

    @nextcord.ui.button(label="+", style=nextcord.ButtonStyle.grey)
    async def add(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.value = self.value + self.multipliers[self.multiplier]

        await interaction.response.edit_message(content=f"{self.baseText}: {self.value}", view=self)

    @nextcord.ui.button(label="-", style=nextcord.ButtonStyle.grey)
    async def subtract(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.value = self.value - self.multipliers[self.multiplier]

        await interaction.response.edit_message(content=f"{self.baseText}: {self.value}", view=self)

    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.stop()

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.value = False
        self.stop()


async def basicApproval(message, repl, tile):
    view = TileBasicApproveView()
    await repl.edit(f"Approve tile {tile.name}", view=view)
    await view.wait()

    return view.value

async def countApproval(message, repl, tile):
    view = TileCountApproveView(f"Adding to tile {tile.name}")
    await repl.edit(f"Adding to tile {tile.name}: 0", view=view)
    await view.wait()

    return view.value


async def promptTile(guild, message, repl, tileSet, prefix = ""):
    view = TileSelectView(tileSet)
    await repl.edit(view=view)
    await view.wait()

    tileSlug = view.tile
    count = 0
    approved = False

    if tileSlug:
        tld = tileSet.getTileByName(tileSlug)

        if isinstance(tld, tiles.TileSet):
            # Subtiles - Go through selection again
            return await promptTile(guild, message, repl, tld, f"{prefix}{tileSlug}.")
        elif isinstance(tld, tiles.CountTile):
            count = await countApproval(message, repl, tld)
            if count:
                approved = True
        else:
            approved = await basicApproval(message, repl, tld)

    return (prefix + tileSlug, approved, count)

async def promptKnownTile(guild, message, text):
    brd = board.load(guild)
    tld = brd.getTileByName(tileSlug)

    # Placeholder reply, edited by the various views
    repl = await message.reply(text, view=None)
    
    count = 0
    approved = False

    if isinstance(tld, tiles.CountTile):
        count = await countApproval(message, repl, tld)
        if count:
            approved = True
    else:
        approved = await basicApproval(message, repl, tld)

    return (approved, count)


async def prompt(guild, message, text):

    brd = board.load(guild)

    # Placeholder reply, edited by the various views
    repl = await message.reply(text, view=None)

    tile = None
    approved = False
    count = 0

    try:
        tile, approved, count = await promptTile(guild, message, repl, brd)
    except:
        pass # Todo: Log error
    finally:
        await repl.delete()

    return (tile, approved, count)
