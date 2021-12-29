def testing(self):
    assembly = getattr(self, "assembly", [])
    if isinstance(assembly, type([])):
        assembly = " ".join(assembly)
    bytecode = []
    push = bytecode.append
    lenAssembly = len(assembly)
    pos = _skipWhite(assembly, 0)
    while pos < lenAssembly:
        m = _tokenRE.match(assembly, pos)
        if m is None:
            raise tt_instructions_error(
                "Syntax error in TT program (%s)" % assembly[pos - 5 : pos + 15]
            )
        dummy, mnemonic, arg, number, comment = m.groups()
        pos = m.regs[0][1]
        if comment:
            pos = _skipWhite(assembly, pos)
            continue

        arg = arg.strip()
        if mnemonic.startswith("INSTR"):
            # Unknown instruction
            op = int(mnemonic[5:])
            push(op)
        elif mnemonic not in ("PUSH", "NPUSHB", "NPUSHW", "PUSHB", "PUSHW"):
            op, argBits, name = mnemonicDict[mnemonic]
            if len(arg) != argBits:
                raise tt_instructions_error(
                    "Incorrect number of argument bits (%s[%s])" % (mnemonic, arg)
                )
            if arg:
                arg = binary2num(arg)
                push(op + arg)
            else:
                push(op)
        else:
            args = []
            pos = _skipWhite(assembly, pos)
            while pos < lenAssembly:
                m = _tokenRE.match(assembly, pos)
                if m is None:
                    raise tt_instructions_error(
                        "Syntax error in TT program (%s)" % assembly[pos : pos + 15]
                    )
                dummy, _mnemonic, arg, number, comment = m.groups()
                if number is None and comment is None:
                    break
                pos = m.regs[0][1]
                pos = _skipWhite(assembly, pos)
                if comment is not None:
                    continue
                args.append(int(number))
            nArgs = len(args)
            if mnemonic == "PUSH":
                # Automatically choose the most compact representation
                nWords = 0
                while nArgs:
                    while (
                        nWords < nArgs
                        and nWords < 255
                        and not (0 <= args[nWords] <= 255)
                    ):
                        nWords += 1
                    nBytes = 0
                    while (
                        nWords + nBytes < nArgs
                        and nBytes < 255
                        and 0 <= args[nWords + nBytes] <= 255
                    ):
                        nBytes += 1
                    if (
                        nBytes < 2
                        and nWords + nBytes < 255
                        and nWords + nBytes != nArgs
                    ):
                        # Will write bytes as words
                        nWords += nBytes
                        continue

                    # Write words
                    if nWords:
                        if nWords <= 8:
                            op, argBits, name = streamMnemonicDict["PUSHW"]
                            op = op + nWords - 1
                            push(op)
                        else:
                            op, argBits, name = streamMnemonicDict["NPUSHW"]
                            push(op)
                            push(nWords)
                        for value in args[:nWords]:
                            assert -32768 <= value < 32768, (
                                "PUSH value out of range %d" % value
                            )
                            push((value >> 8) & 0xFF)
                            push(value & 0xFF)

                    # Write bytes
                    if nBytes:
                        pass
                        if nBytes <= 8:
                            op, argBits, name = streamMnemonicDict["PUSHB"]
                            op = op + nBytes - 1
                            push(op)
                        else:
                            op, argBits, name = streamMnemonicDict["NPUSHB"]
                            push(op)
                            push(nBytes)
                        for value in args[nWords : nWords + nBytes]:
                            push(value)

                    nTotal = nWords + nBytes
                    args = args[nTotal:]
                    nArgs -= nTotal
                    nWords = 0
            else:
                # Write exactly what we've been asked to
                words = mnemonic[-1] == "W"
                op, argBits, name = streamMnemonicDict[mnemonic]
                if mnemonic[0] != "N":
                    assert nArgs <= 8, nArgs
                    op = op + nArgs - 1
                    push(op)
                else:
                    assert nArgs < 256
                    push(op)
                    push(nArgs)
                if words:
                    for value in args:
                        assert -32768 <= value < 32768, (
                            "PUSHW value out of range %d" % value
                        )
                        push((value >> 8) & 0xFF)
                        push(value & 0xFF)
                else:
                    for value in args:
                        assert 0 <= value < 256, "PUSHB value out of range %d" % value
                        push(value)

        pos = _skipWhite(assembly, pos)

    if bytecode:
        assert max(bytecode) < 256 and min(bytecode) >= 0
    self.bytecode = array.array("B", bytecode)
