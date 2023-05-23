




def Lookup(auth, cmds, args, halp=False):
	ret = None 
	hlp = False
	retargs = []

	if not args:
		if halp:
			ret = cmds 
		elif "" in cmds:
			ret = cmds[""]
		else:
			ret = None
			hlp = True
	else:
		a = args[0].lower()

		if a in ["help", "elp"]:
			hlp = True
			ret, _, _ = Lookup(auth, cmds, args[1:], True)
		else:
			if not a in cmds:
				ret = None
			else:
				f = cmds[a]
				if isinstance(f, tuple):
					(a, f) = f
					if auth < a:
						f = None

				if isinstance(f, dict):
					ret, retargs, hlp = Lookup(auth, f, args[1:], halp)
				else:
					if len(args) > 1:
						hlp = args[1].lower() in ["help", "elp"]
					retargs = args[1:]
					ret = f

	return (ret, retargs, hlp)


def HelpString(auth, f, ar):
	helpstr = ""
	if isinstance(f, dict):
		if "" in f:
			helpstr += f[""].__doc__ + "\n"
		else:
			pass

		helpstr += "Commands: "
		for k,v in f.items():
			vd = ""

			if isinstance(v, tuple):
				a, v = v
				if auth < a:
					continue

			if isinstance(v, dict):
				if "" in v: 
					vd = v[""].__doc__.partition('\n')[0]
				else:
					vd = "???"
			else:
				if k == "":
					continue
				vd = v.__doc__.partition('\n')[0]

			helpstr += f"\n- {k}: {vd}"
	else:
		helpstr = f.__doc__

	return helpstr
