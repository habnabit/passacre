def createParserClass(GrammarBase, ruleGlobals):
    if ruleGlobals is None:
        ruleGlobals = {}
    class Parser(GrammarBase):
        def rule_ws(self):
            _locals = {'self': self}
            self.locals['ws'] = _locals
            def _G_many_1():
                def _G_label_2():
                    def _G_or_3():
                        self._trace("' '", (7, 10), self.input.position)
                        _G_exactly_4, lastError = self.exactly(' ')
                        self.considerError(lastError, None)
                        return (_G_exactly_4, self.currentError)
                    def _G_or_5():
                        self._trace(" '\\r'", (12, 17), self.input.position)
                        _G_exactly_6, lastError = self.exactly('\r')
                        self.considerError(lastError, None)
                        return (_G_exactly_6, self.currentError)
                    def _G_or_7():
                        self._trace(" '\\n'", (19, 24), self.input.position)
                        _G_exactly_8, lastError = self.exactly('\n')
                        self.considerError(lastError, None)
                        return (_G_exactly_8, self.currentError)
                    def _G_or_9():
                        self._trace(" '\\t'", (26, 31), self.input.position)
                        _G_exactly_10, lastError = self.exactly('\t')
                        self.considerError(lastError, None)
                        return (_G_exactly_10, self.currentError)
                    _G_or_11, lastError = self._or([_G_or_3, _G_or_5, _G_or_7, _G_or_9])
                    self.considerError(lastError, None)
                    return (_G_or_11, self.currentError)
                _G_label_12, lastError = self.label(_G_label_2, "whitespace")
                self.considerError(lastError, None)
                return (_G_label_12, self.currentError)
            _G_many_13, lastError = self.many(_G_many_1)
            self.considerError(lastError, 'ws')
            return (_G_many_13, self.currentError)


        def rule_object(self):
            _locals = {'self': self}
            self.locals['object'] = _locals
            self._trace(' ws', (57, 60), self.input.position)
            _G_apply_14, lastError = self._apply(self.rule_ws, "ws", [])
            self.considerError(lastError, 'object')
            def _G_label_15():
                self._trace(" '{'", (60, 64), self.input.position)
                _G_exactly_16, lastError = self.exactly('{')
                self.considerError(lastError, None)
                return (_G_exactly_16, self.currentError)
            _G_label_17, lastError = self.label(_G_label_15, "object")
            self.considerError(lastError, 'object')
            self._trace(' members', (74, 82), self.input.position)
            _G_apply_18, lastError = self._apply(self.rule_members, "members", [])
            self.considerError(lastError, 'object')
            _locals['m'] = _G_apply_18
            self._trace(' ws', (84, 87), self.input.position)
            _G_apply_19, lastError = self._apply(self.rule_ws, "ws", [])
            self.considerError(lastError, 'object')
            self._trace(" '}'", (87, 91), self.input.position)
            _G_exactly_20, lastError = self.exactly('}')
            self.considerError(lastError, 'object')
            self._trace(' ws', (91, 94), self.input.position)
            _G_apply_21, lastError = self._apply(self.rule_ws, "ws", [])
            self.considerError(lastError, 'object')
            _G_python_23, lastError = eval(self._G_expr_22, self.globals, _locals), None
            self.considerError(lastError, 'object')
            return (_G_python_23, self.currentError)


        def rule_members(self):
            _locals = {'self': self}
            self.locals['members'] = _locals
            def _G_or_24():
                self._trace('pair', (111, 115), self.input.position)
                _G_apply_25, lastError = self._apply(self.rule_pair, "pair", [])
                self.considerError(lastError, None)
                _locals['first'] = _G_apply_25
                def _G_many_26():
                    self._trace('ws', (123, 125), self.input.position)
                    _G_apply_27, lastError = self._apply(self.rule_ws, "ws", [])
                    self.considerError(lastError, None)
                    self._trace(" ','", (125, 129), self.input.position)
                    _G_exactly_28, lastError = self.exactly(',')
                    self.considerError(lastError, None)
                    self._trace(' pair', (129, 134), self.input.position)
                    _G_apply_29, lastError = self._apply(self.rule_pair, "pair", [])
                    self.considerError(lastError, None)
                    return (_G_apply_29, self.currentError)
                _G_many_30, lastError = self.many(_G_many_26)
                self.considerError(lastError, None)
                _locals['rest'] = _G_many_30
                _G_python_32, lastError = eval(self._G_expr_31, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_32, self.currentError)
            def _G_or_33():
                _G_python_34, lastError = ({}), None
                self.considerError(lastError, None)
                return (_G_python_34, self.currentError)
            _G_or_35, lastError = self._or([_G_or_24, _G_or_33])
            self.considerError(lastError, 'members')
            return (_G_or_35, self.currentError)


        def rule_pair(self):
            _locals = {'self': self}
            self.locals['pair'] = _locals
            self._trace(' ws', (181, 184), self.input.position)
            _G_apply_36, lastError = self._apply(self.rule_ws, "ws", [])
            self.considerError(lastError, 'pair')
            def _G_or_37():
                self._trace('string', (186, 192), self.input.position)
                _G_apply_38, lastError = self._apply(self.rule_string, "string", [])
                self.considerError(lastError, None)
                return (_G_apply_38, self.currentError)
            def _G_or_39():
                self._trace(' identifier', (194, 205), self.input.position)
                _G_apply_40, lastError = self._apply(self.rule_identifier, "identifier", [])
                self.considerError(lastError, None)
                return (_G_apply_40, self.currentError)
            _G_or_41, lastError = self._or([_G_or_37, _G_or_39])
            self.considerError(lastError, 'pair')
            _locals['k'] = _G_or_41
            self._trace(' ws', (208, 211), self.input.position)
            _G_apply_42, lastError = self._apply(self.rule_ws, "ws", [])
            self.considerError(lastError, 'pair')
            self._trace(" ':'", (211, 215), self.input.position)
            _G_exactly_43, lastError = self.exactly(':')
            self.considerError(lastError, 'pair')
            self._trace(' value', (215, 221), self.input.position)
            _G_apply_44, lastError = self._apply(self.rule_value, "value", [])
            self.considerError(lastError, 'pair')
            _locals['v'] = _G_apply_44
            _G_python_46, lastError = eval(self._G_expr_45, self.globals, _locals), None
            self.considerError(lastError, 'pair')
            return (_G_python_46, self.currentError)


        def rule_array(self):
            _locals = {'self': self}
            self.locals['array'] = _locals
            self._trace(' ws', (241, 244), self.input.position)
            _G_apply_47, lastError = self._apply(self.rule_ws, "ws", [])
            self.considerError(lastError, 'array')
            def _G_label_48():
                self._trace(" '['", (244, 248), self.input.position)
                _G_exactly_49, lastError = self.exactly('[')
                self.considerError(lastError, None)
                return (_G_exactly_49, self.currentError)
            _G_label_50, lastError = self.label(_G_label_48, "array")
            self.considerError(lastError, 'array')
            self._trace(' elements', (257, 266), self.input.position)
            _G_apply_51, lastError = self._apply(self.rule_elements, "elements", [])
            self.considerError(lastError, 'array')
            _locals['xs'] = _G_apply_51
            self._trace(' ws', (269, 272), self.input.position)
            _G_apply_52, lastError = self._apply(self.rule_ws, "ws", [])
            self.considerError(lastError, 'array')
            self._trace(" ']'", (272, 276), self.input.position)
            _G_exactly_53, lastError = self.exactly(']')
            self.considerError(lastError, 'array')
            _G_python_55, lastError = eval(self._G_expr_54, self.globals, _locals), None
            self.considerError(lastError, 'array')
            return (_G_python_55, self.currentError)


        def rule_elements(self):
            _locals = {'self': self}
            self.locals['elements'] = _locals
            def _G_or_56():
                self._trace('value', (295, 300), self.input.position)
                _G_apply_57, lastError = self._apply(self.rule_value, "value", [])
                self.considerError(lastError, None)
                _locals['first'] = _G_apply_57
                def _G_many_58():
                    self._trace('ws', (308, 310), self.input.position)
                    _G_apply_59, lastError = self._apply(self.rule_ws, "ws", [])
                    self.considerError(lastError, None)
                    self._trace(" ','", (310, 314), self.input.position)
                    _G_exactly_60, lastError = self.exactly(',')
                    self.considerError(lastError, None)
                    self._trace(' value', (314, 320), self.input.position)
                    _G_apply_61, lastError = self._apply(self.rule_value, "value", [])
                    self.considerError(lastError, None)
                    return (_G_apply_61, self.currentError)
                _G_many_62, lastError = self.many(_G_many_58)
                self.considerError(lastError, None)
                _locals['rest'] = _G_many_62
                _G_python_64, lastError = eval(self._G_expr_63, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_64, self.currentError)
            def _G_or_65():
                _G_python_66, lastError = ([]), None
                self.considerError(lastError, None)
                return (_G_python_66, self.currentError)
            _G_or_67, lastError = self._or([_G_or_56, _G_or_65])
            self.considerError(lastError, 'elements')
            return (_G_or_67, self.currentError)


        def rule_value(self):
            _locals = {'self': self}
            self.locals['value'] = _locals
            self._trace(' ws', (362, 365), self.input.position)
            _G_apply_68, lastError = self._apply(self.rule_ws, "ws", [])
            self.considerError(lastError, 'value')
            def _G_or_69():
                self._trace('string', (367, 373), self.input.position)
                _G_apply_70, lastError = self._apply(self.rule_string, "string", [])
                self.considerError(lastError, None)
                return (_G_apply_70, self.currentError)
            def _G_or_71():
                self._trace(' number', (375, 382), self.input.position)
                _G_apply_72, lastError = self._apply(self.rule_number, "number", [])
                self.considerError(lastError, None)
                return (_G_apply_72, self.currentError)
            def _G_or_73():
                self._trace(' array', (384, 390), self.input.position)
                _G_apply_74, lastError = self._apply(self.rule_array, "array", [])
                self.considerError(lastError, None)
                return (_G_apply_74, self.currentError)
            def _G_or_75():
                self._trace(" 'true'", (403, 410), self.input.position)
                _G_exactly_76, lastError = self.exactly('true')
                self.considerError(lastError, None)
                _G_python_77, lastError = (True), None
                self.considerError(lastError, None)
                return (_G_python_77, self.currentError)
            def _G_or_78():
                self._trace(" 'false'", (431, 439), self.input.position)
                _G_exactly_79, lastError = self.exactly('false')
                self.considerError(lastError, None)
                _G_python_80, lastError = (False), None
                self.considerError(lastError, None)
                return (_G_python_80, self.currentError)
            def _G_or_81():
                def _G_or_82():
                    self._trace("'null'", (463, 469), self.input.position)
                    _G_exactly_83, lastError = self.exactly('null')
                    self.considerError(lastError, None)
                    return (_G_exactly_83, self.currentError)
                def _G_or_84():
                    self._trace(" '%'", (471, 475), self.input.position)
                    _G_exactly_85, lastError = self.exactly('%')
                    self.considerError(lastError, None)
                    return (_G_exactly_85, self.currentError)
                _G_or_86, lastError = self._or([_G_or_82, _G_or_84])
                self.considerError(lastError, None)
                _G_python_87, lastError = (None), None
                self.considerError(lastError, None)
                return (_G_python_87, self.currentError)
            def _G_or_88():
                self._trace(' identifier', (497, 508), self.input.position)
                _G_apply_89, lastError = self._apply(self.rule_identifier, "identifier", [])
                self.considerError(lastError, None)
                return (_G_apply_89, self.currentError)
            def _G_or_90():
                self._trace(' object', (510, 517), self.input.position)
                _G_apply_91, lastError = self._apply(self.rule_object, "object", [])
                self.considerError(lastError, None)
                return (_G_apply_91, self.currentError)
            _G_or_92, lastError = self._or([_G_or_69, _G_or_71, _G_or_73, _G_or_75, _G_or_78, _G_or_81, _G_or_88, _G_or_90])
            self.considerError(lastError, 'value')
            return (_G_or_92, self.currentError)


        def rule_identifier(self):
            _locals = {'self': self}
            self.locals['identifier'] = _locals
            def _G_label_93():
                def _G_consumedby_94():
                    def _G_many1_95():
                        def _G_or_96():
                            self._trace('letterOrDigit', (534, 547), self.input.position)
                            _G_apply_97, lastError = self._apply(self.rule_letterOrDigit, "letterOrDigit", [])
                            self.considerError(lastError, None)
                            return (_G_apply_97, self.currentError)
                        def _G_or_98():
                            self._trace(" '-'", (549, 553), self.input.position)
                            _G_exactly_99, lastError = self.exactly('-')
                            self.considerError(lastError, None)
                            return (_G_exactly_99, self.currentError)
                        def _G_or_100():
                            self._trace(" '_'", (555, 559), self.input.position)
                            _G_exactly_101, lastError = self.exactly('_')
                            self.considerError(lastError, None)
                            return (_G_exactly_101, self.currentError)
                        _G_or_102, lastError = self._or([_G_or_96, _G_or_98, _G_or_100])
                        self.considerError(lastError, None)
                        return (_G_or_102, self.currentError)
                    _G_many1_103, lastError = self.many(_G_many1_95, _G_many1_95())
                    self.considerError(lastError, None)
                    return (_G_many1_103, self.currentError)
                _G_consumedby_104, lastError = self.consumedby(_G_consumedby_94)
                self.considerError(lastError, None)
                return (_G_consumedby_104, self.currentError)
            _G_label_105, lastError = self.label(_G_label_93, "identifier")
            self.considerError(lastError, 'identifier')
            return (_G_label_105, self.currentError)


        def rule_nonControl(self):
            _locals = {'self': self}
            self.locals['nonControl'] = _locals
            self._trace(' anything', (589, 598), self.input.position)
            _G_apply_106, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'nonControl')
            _locals['x'] = _G_apply_106
            def _G_pred_107():
                _G_python_109, lastError = eval(self._G_expr_108, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_109, self.currentError)
            _G_pred_110, lastError = self.pred(_G_pred_107)
            self.considerError(lastError, 'nonControl')
            _G_python_112, lastError = eval(self._G_expr_111, self.globals, _locals), None
            self.considerError(lastError, 'nonControl')
            return (_G_python_112, self.currentError)


        def rule_string(self):
            _locals = {'self': self}
            self.locals['string'] = _locals
            def _G_label_113():
                self._trace(' \'"\'', (649, 653), self.input.position)
                _G_exactly_114, lastError = self.exactly('"')
                self.considerError(lastError, None)
                return (_G_exactly_114, self.currentError)
            _G_label_115, lastError = self.label(_G_label_113, "string")
            self.considerError(lastError, 'string')
            def _G_many_116():
                def _G_or_117():
                    self._trace('escapedChar', (665, 676), self.input.position)
                    _G_apply_118, lastError = self._apply(self.rule_escapedChar, "escapedChar", [])
                    self.considerError(lastError, None)
                    return (_G_apply_118, self.currentError)
                def _G_or_119():
                    def _G_not_120():
                        def _G_or_121():
                            self._trace('\'"\'', (681, 684), self.input.position)
                            _G_exactly_122, lastError = self.exactly('"')
                            self.considerError(lastError, None)
                            return (_G_exactly_122, self.currentError)
                        def _G_or_123():
                            self._trace(" '\\\\'", (686, 691), self.input.position)
                            _G_exactly_124, lastError = self.exactly('\\')
                            self.considerError(lastError, None)
                            return (_G_exactly_124, self.currentError)
                        _G_or_125, lastError = self._or([_G_or_121, _G_or_123])
                        self.considerError(lastError, None)
                        return (_G_or_125, self.currentError)
                    _G_not_126, lastError = self._not(_G_not_120)
                    self.considerError(lastError, None)
                    self._trace(' nonControl', (692, 703), self.input.position)
                    _G_apply_127, lastError = self._apply(self.rule_nonControl, "nonControl", [])
                    self.considerError(lastError, None)
                    return (_G_apply_127, self.currentError)
                _G_or_128, lastError = self._or([_G_or_117, _G_or_119])
                self.considerError(lastError, None)
                return (_G_or_128, self.currentError)
            _G_many_129, lastError = self.many(_G_many_116)
            self.considerError(lastError, 'string')
            _locals['c'] = _G_many_129
            self._trace(' \'"\'', (707, 711), self.input.position)
            _G_exactly_130, lastError = self.exactly('"')
            self.considerError(lastError, 'string')
            _G_python_132, lastError = eval(self._G_expr_131, self.globals, _locals), None
            self.considerError(lastError, 'string')
            return (_G_python_132, self.currentError)


        def rule_escapedChar(self):
            _locals = {'self': self}
            self.locals['escapedChar'] = _locals
            self._trace(" '\\\\'", (739, 744), self.input.position)
            _G_exactly_133, lastError = self.exactly('\\')
            self.considerError(lastError, 'escapedChar')
            def _G_or_134():
                self._trace('\'"\'', (747, 750), self.input.position)
                _G_exactly_135, lastError = self.exactly('"')
                self.considerError(lastError, None)
                _G_python_136, lastError = ('"'), None
                self.considerError(lastError, None)
                return (_G_python_136, self.currentError)
            def _G_or_137():
                self._trace("'\\\\'", (764, 768), self.input.position)
                _G_exactly_138, lastError = self.exactly('\\')
                self.considerError(lastError, None)
                _G_python_139, lastError = ('\\'), None
                self.considerError(lastError, None)
                return (_G_python_139, self.currentError)
            def _G_or_140():
                self._trace("'/'", (799, 802), self.input.position)
                _G_exactly_141, lastError = self.exactly('/')
                self.considerError(lastError, None)
                _G_python_142, lastError = ('/'), None
                self.considerError(lastError, None)
                return (_G_python_142, self.currentError)
            def _G_or_143():
                self._trace("'b'", (816, 819), self.input.position)
                _G_exactly_144, lastError = self.exactly('b')
                self.considerError(lastError, None)
                _G_python_145, lastError = ('\b'), None
                self.considerError(lastError, None)
                return (_G_python_145, self.currentError)
            def _G_or_146():
                self._trace("'f'", (850, 853), self.input.position)
                _G_exactly_147, lastError = self.exactly('f')
                self.considerError(lastError, None)
                _G_python_148, lastError = ('\f'), None
                self.considerError(lastError, None)
                return (_G_python_148, self.currentError)
            def _G_or_149():
                self._trace("'n'", (867, 870), self.input.position)
                _G_exactly_150, lastError = self.exactly('n')
                self.considerError(lastError, None)
                _G_python_151, lastError = ('\n'), None
                self.considerError(lastError, None)
                return (_G_python_151, self.currentError)
            def _G_or_152():
                self._trace("'r'", (901, 904), self.input.position)
                _G_exactly_153, lastError = self.exactly('r')
                self.considerError(lastError, None)
                _G_python_154, lastError = ('\r'), None
                self.considerError(lastError, None)
                return (_G_python_154, self.currentError)
            def _G_or_155():
                self._trace("'t'", (918, 921), self.input.position)
                _G_exactly_156, lastError = self.exactly('t')
                self.considerError(lastError, None)
                _G_python_157, lastError = ('\t'), None
                self.considerError(lastError, None)
                return (_G_python_157, self.currentError)
            def _G_or_158():
                self._trace("'\\''", (952, 956), self.input.position)
                _G_exactly_159, lastError = self.exactly("'")
                self.considerError(lastError, None)
                _G_python_160, lastError = ('\''), None
                self.considerError(lastError, None)
                return (_G_python_160, self.currentError)
            def _G_or_161():
                self._trace(' escapedUnicode', (968, 983), self.input.position)
                _G_apply_162, lastError = self._apply(self.rule_escapedUnicode, "escapedUnicode", [])
                self.considerError(lastError, None)
                return (_G_apply_162, self.currentError)
            _G_or_163, lastError = self._or([_G_or_134, _G_or_137, _G_or_140, _G_or_143, _G_or_146, _G_or_149, _G_or_152, _G_or_155, _G_or_158, _G_or_161])
            self.considerError(lastError, 'escapedChar')
            return (_G_or_163, self.currentError)


        def rule_hexdigit(self):
            _locals = {'self': self}
            self.locals['hexdigit'] = _locals
            _G_apply_164, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'hexdigit')
            _locals['x'] = _G_apply_164
            def _G_pred_165():
                _G_python_167, lastError = eval(self._G_expr_166, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_167, self.currentError)
            _G_pred_168, lastError = self.pred(_G_pred_165)
            self.considerError(lastError, 'hexdigit')
            _G_python_169, lastError = eval(self._G_expr_111, self.globals, _locals), None
            self.considerError(lastError, 'hexdigit')
            return (_G_python_169, self.currentError)


        def rule_escapedUnicode(self):
            _locals = {'self': self}
            self.locals['escapedUnicode'] = _locals
            self._trace(" 'u'", (1053, 1057), self.input.position)
            _G_exactly_170, lastError = self.exactly('u')
            self.considerError(lastError, 'escapedUnicode')
            def _G_consumedby_171():
                def _G_repeat_172():
                    self._trace('hexdigit', (1059, 1067), self.input.position)
                    _G_apply_173, lastError = self._apply(self.rule_hexdigit, "hexdigit", [])
                    self.considerError(lastError, None)
                    return (_G_apply_173, self.currentError)
                _G_repeat_174, lastError = self.repeat(4, 4, _G_repeat_172)
                self.considerError(lastError, None)
                return (_G_repeat_174, self.currentError)
            _G_consumedby_175, lastError = self.consumedby(_G_consumedby_171)
            self.considerError(lastError, 'escapedUnicode')
            _locals['hs'] = _G_consumedby_175
            _G_python_177, lastError = eval(self._G_expr_176, self.globals, _locals), None
            self.considerError(lastError, 'escapedUnicode')
            return (_G_python_177, self.currentError)


        def rule_number(self):
            _locals = {'self': self}
            self.locals['number'] = _locals
            def _G_label_178():
                def _G_or_179():
                    self._trace("'-'", (1109, 1112), self.input.position)
                    _G_exactly_180, lastError = self.exactly('-')
                    self.considerError(lastError, None)
                    return (_G_exactly_180, self.currentError)
                def _G_or_181():
                    _G_python_182, lastError = (''), None
                    self.considerError(lastError, None)
                    return (_G_python_182, self.currentError)
                _G_or_183, lastError = self._or([_G_or_179, _G_or_181])
                self.considerError(lastError, None)
                return (_G_or_183, self.currentError)
            _G_label_184, lastError = self.label(_G_label_178, "number")
            self.considerError(lastError, 'number')
            _locals['sign'] = _G_label_184
            self._trace('intPart', (1139, 1146), self.input.position)
            _G_apply_185, lastError = self._apply(self.rule_intPart, "intPart", [])
            self.considerError(lastError, 'number')
            _locals['ds'] = _G_apply_185
            def _G_or_186():
                self._trace('floatPart(sign ds)', (1151, 1169), self.input.position)
                _G_python_188, lastError = eval(self._G_expr_187, self.globals, _locals), None
                self.considerError(lastError, None)
                _G_python_190, lastError = eval(self._G_expr_189, self.globals, _locals), None
                self.considerError(lastError, None)
                _G_apply_191, lastError = self._apply(self.rule_floatPart, "floatPart", [_G_python_188, _G_python_190])
                self.considerError(lastError, None)
                return (_G_apply_191, self.currentError)
            def _G_or_192():
                _G_python_194, lastError = eval(self._G_expr_193, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_194, self.currentError)
            _G_or_195, lastError = self._or([_G_or_186, _G_or_192])
            self.considerError(lastError, 'number')
            return (_G_or_195, self.currentError)


        def rule_digit(self):
            _locals = {'self': self}
            self.locals['digit'] = _locals
            _G_apply_196, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'digit')
            _locals['x'] = _G_apply_196
            def _G_pred_197():
                _G_python_199, lastError = eval(self._G_expr_198, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_199, self.currentError)
            _G_pred_200, lastError = self.pred(_G_pred_197)
            self.considerError(lastError, 'digit')
            _G_python_201, lastError = eval(self._G_expr_111, self.globals, _locals), None
            self.considerError(lastError, 'digit')
            return (_G_python_201, self.currentError)


        def rule_digits(self):
            _locals = {'self': self}
            self.locals['digits'] = _locals
            def _G_consumedby_202():
                def _G_many_203():
                    self._trace('digit', (1267, 1272), self.input.position)
                    _G_apply_204, lastError = self._apply(self.rule_digit, "digit", [])
                    self.considerError(lastError, None)
                    return (_G_apply_204, self.currentError)
                _G_many_205, lastError = self.many(_G_many_203)
                self.considerError(lastError, None)
                return (_G_many_205, self.currentError)
            _G_consumedby_206, lastError = self.consumedby(_G_consumedby_202)
            self.considerError(lastError, 'digits')
            return (_G_consumedby_206, self.currentError)


        def rule_digit1_9(self):
            _locals = {'self': self}
            self.locals['digit1_9'] = _locals
            _G_apply_207, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'digit1_9')
            _locals['x'] = _G_apply_207
            def _G_pred_208():
                _G_python_210, lastError = eval(self._G_expr_209, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_210, self.currentError)
            _G_pred_211, lastError = self.pred(_G_pred_208)
            self.considerError(lastError, 'digit1_9')
            _G_python_212, lastError = eval(self._G_expr_111, self.globals, _locals), None
            self.considerError(lastError, 'digit1_9')
            return (_G_python_212, self.currentError)


        def rule_intPart(self):
            _locals = {'self': self}
            self.locals['intPart'] = _locals
            def _G_or_213():
                self._trace('digit1_9', (1325, 1333), self.input.position)
                _G_apply_214, lastError = self._apply(self.rule_digit1_9, "digit1_9", [])
                self.considerError(lastError, None)
                _locals['first'] = _G_apply_214
                self._trace(' digits', (1339, 1346), self.input.position)
                _G_apply_215, lastError = self._apply(self.rule_digits, "digits", [])
                self.considerError(lastError, None)
                _locals['rest'] = _G_apply_215
                _G_python_217, lastError = eval(self._G_expr_216, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_217, self.currentError)
            def _G_or_218():
                self._trace(' digit', (1370, 1376), self.input.position)
                _G_apply_219, lastError = self._apply(self.rule_digit, "digit", [])
                self.considerError(lastError, None)
                return (_G_apply_219, self.currentError)
            _G_or_220, lastError = self._or([_G_or_213, _G_or_218])
            self.considerError(lastError, 'intPart')
            return (_G_or_220, self.currentError)


        def rule_floatPart(self):
            _locals = {'self': self}
            self.locals['floatPart'] = _locals
            _G_apply_221, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'floatPart')
            _locals['sign'] = _G_apply_221
            _G_apply_222, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'floatPart')
            _locals['ds'] = _G_apply_222
            def _G_consumedby_223():
                def _G_or_224():
                    self._trace("'.'", (1401, 1404), self.input.position)
                    _G_exactly_225, lastError = self.exactly('.')
                    self.considerError(lastError, None)
                    self._trace(' digits', (1404, 1411), self.input.position)
                    _G_apply_226, lastError = self._apply(self.rule_digits, "digits", [])
                    self.considerError(lastError, None)
                    def _G_optional_227():
                        self._trace(' exponent', (1411, 1420), self.input.position)
                        _G_apply_228, lastError = self._apply(self.rule_exponent, "exponent", [])
                        self.considerError(lastError, None)
                        return (_G_apply_228, self.currentError)
                    def _G_optional_229():
                        return (None, self.input.nullError())
                    _G_or_230, lastError = self._or([_G_optional_227, _G_optional_229])
                    self.considerError(lastError, None)
                    return (_G_or_230, self.currentError)
                def _G_or_231():
                    self._trace(' exponent', (1424, 1433), self.input.position)
                    _G_apply_232, lastError = self._apply(self.rule_exponent, "exponent", [])
                    self.considerError(lastError, None)
                    return (_G_apply_232, self.currentError)
                _G_or_233, lastError = self._or([_G_or_224, _G_or_231])
                self.considerError(lastError, None)
                return (_G_or_233, self.currentError)
            _G_consumedby_234, lastError = self.consumedby(_G_consumedby_223)
            self.considerError(lastError, 'floatPart')
            _locals['tail'] = _G_consumedby_234
            _G_python_236, lastError = eval(self._G_expr_235, self.globals, _locals), None
            self.considerError(lastError, 'floatPart')
            return (_G_python_236, self.currentError)


        def rule_exponent(self):
            _locals = {'self': self}
            self.locals['exponent'] = _locals
            def _G_or_237():
                self._trace("'e'", (1499, 1502), self.input.position)
                _G_exactly_238, lastError = self.exactly('e')
                self.considerError(lastError, None)
                return (_G_exactly_238, self.currentError)
            def _G_or_239():
                self._trace(" 'E'", (1504, 1508), self.input.position)
                _G_exactly_240, lastError = self.exactly('E')
                self.considerError(lastError, None)
                return (_G_exactly_240, self.currentError)
            _G_or_241, lastError = self._or([_G_or_237, _G_or_239])
            self.considerError(lastError, 'exponent')
            def _G_optional_242():
                def _G_or_243():
                    self._trace("'+'", (1511, 1514), self.input.position)
                    _G_exactly_244, lastError = self.exactly('+')
                    self.considerError(lastError, None)
                    return (_G_exactly_244, self.currentError)
                def _G_or_245():
                    self._trace(" '-'", (1516, 1520), self.input.position)
                    _G_exactly_246, lastError = self.exactly('-')
                    self.considerError(lastError, None)
                    return (_G_exactly_246, self.currentError)
                _G_or_247, lastError = self._or([_G_or_243, _G_or_245])
                self.considerError(lastError, None)
                return (_G_or_247, self.currentError)
            def _G_optional_248():
                return (None, self.input.nullError())
            _G_or_249, lastError = self._or([_G_optional_242, _G_optional_248])
            self.considerError(lastError, 'exponent')
            self._trace(' digits', (1522, 1529), self.input.position)
            _G_apply_250, lastError = self._apply(self.rule_digits, "digits", [])
            self.considerError(lastError, 'exponent')
            return (_G_apply_250, self.currentError)


        def rule_top(self):
            _locals = {'self': self}
            self.locals['top'] = _locals
            def _G_or_251():
                self._trace(' value', (1538, 1544), self.input.position)
                _G_apply_252, lastError = self._apply(self.rule_value, "value", [])
                self.considerError(lastError, None)
                _locals['x'] = _G_apply_252
                self._trace(' ws', (1546, 1549), self.input.position)
                _G_apply_253, lastError = self._apply(self.rule_ws, "ws", [])
                self.considerError(lastError, None)
                self._trace(' end', (1549, 1553), self.input.position)
                _G_apply_254, lastError = self._apply(self.rule_end, "end", [])
                self.considerError(lastError, None)
                _G_python_255, lastError = eval(self._G_expr_111, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_255, self.currentError)
            def _G_or_256():
                self._trace(' members', (1566, 1574), self.input.position)
                _G_apply_257, lastError = self._apply(self.rule_members, "members", [])
                self.considerError(lastError, None)
                _locals['x'] = _G_apply_257
                self._trace(' ws', (1576, 1579), self.input.position)
                _G_apply_258, lastError = self._apply(self.rule_ws, "ws", [])
                self.considerError(lastError, None)
                self._trace(' end', (1579, 1583), self.input.position)
                _G_apply_259, lastError = self._apply(self.rule_end, "end", [])
                self.considerError(lastError, None)
                _G_python_260, lastError = eval(self._G_expr_111, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_260, self.currentError)
            _G_or_261, lastError = self._or([_G_or_251, _G_or_256])
            self.considerError(lastError, 'top')
            return (_G_or_261, self.currentError)


        _G_expr_63 = compile('[first] + rest', '<string>', 'eval')
        _G_expr_193 = compile('int(sign + ds)', '<string>', 'eval')
        _G_expr_235 = compile('float(sign + ds + tail)', '<string>', 'eval')
        _G_expr_176 = compile('unichr(int(hs, 16))', '<string>', 'eval')
        _G_expr_31 = compile('dict([first] + rest)', '<string>', 'eval')
        _G_expr_131 = compile("''.join(c)", '<string>', 'eval')
        _G_expr_198 = compile("x in '0123456789'", '<string>', 'eval')
        _G_expr_22 = compile('m', '<string>', 'eval')
        _G_expr_45 = compile('(k, v)', '<string>', 'eval')
        _G_expr_187 = compile('sign', '<string>', 'eval')
        _G_expr_216 = compile('first + rest', '<string>', 'eval')
        _G_expr_111 = compile('x', '<string>', 'eval')
        _G_expr_54 = compile('xs', '<string>', 'eval')
        _G_expr_209 = compile("x in '123456789'", '<string>', 'eval')
        _G_expr_166 = compile("x in '0123456789abcdefABCDEF'", '<string>', 'eval')
        _G_expr_189 = compile('ds', '<string>', 'eval')
        _G_expr_108 = compile("unicodedata.category(x) != 'Cc'", '<string>', 'eval')
    if Parser.globals is not None:
        Parser.globals = Parser.globals.copy()
        Parser.globals.update(ruleGlobals)
    else:
        Parser.globals = ruleGlobals
    return Parser
