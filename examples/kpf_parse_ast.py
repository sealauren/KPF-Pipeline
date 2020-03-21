# kpf_parse_ast_1.py

from ast import NodeVisitor, iter_fields
import _ast
from collections.abc import Iterable
from collections import deque
from queue import Queue
from FauxLevel0Primatives import read_data, Normalize, NoiseReduce, Spectrum1D
from kpf_pipeline_args import KpfPipelineArgs
from keckdrpframework.models.action import Action
from keckdrpframework.models.processing_context import ProcessingContext

class KpfPipelineNodeVisitor1(NodeVisitor):
    """
    Node visitor to convert KPF pipeline recipes expressed in python syntax
    into operations on the KPF Framework.

    Prototype version!
    """
    _indentStr = ""
    _indent = 0

    def __init__(self, context=None):
        NodeVisitor.__init__(self)
        self._indentStr = "  "
        self._indent = 0
        # instantiate the primative dict and some primitives
        self._prims = {}
        self._prims["read_data"] = read_data
        self._prims["Normalize"] = Normalize
        self._prims["NoiseReduce"] = NoiseReduce
        self._prims["Spectrum1D"] = Spectrum1D
        # instantiate the parameters dict
        self._params = {}
        # store and load stacks (implemented as lists; use append() and pop())
        self._store = list()
        self._load = list()
        # KPF framework items
        self.context = context
        self.tree = None
        self.awaiting_call_return = False
        self.returning_from_call = False
        self.call_output = None
        # housekeeping
        self._reset_visited_states = False
    
    def visit_Module(self, node):
        """
        Module node
        """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            for item in node.body:
                self.visit(item)
            return
        print("Module")
        if not getattr(node, 'kpf_completed', False):
            self._indent += 1
            self.tree = node
            for item in node.body:
                self.visit(item)
                if self.awaiting_call_return:
                    return
            self.tree = None
            setattr(node, 'kpf_completed', True)

    def visit_ImportFrom(self, node):
        """
        import primatives from a location and add them to the prims dict
        """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            for name in node.names:
                self.visit(name)
            return
        if not getattr(node, 'kpf_completed', False):
            module = node.module
            #TODO do something with module to extract a path
            loadQSizeBefore = len(self._load)
            for name in node.names:
                self.visit(name)
            while len(self._load) > loadQSizeBefore:
                # import the named primitive
                # just print the name for now
                tup = self._load.pop()
                print(f"Import {tup[0]} from {module}")
            setattr(node, 'kpf_completed', True)

    def visit_alias(self, node):
        """ alias: put name and asname on _load stack as tuple """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            return
        if not getattr(node, 'kpf_completed', False):
            self._load.append((node.name, node.asname))
            print("{}alias: {} as {}".format(self._indentStr * self._indent, node.name, node.asname))
            setattr(node, 'kpf_completed', True)
    
    def visit_Name(self, node):
        """
        Implementation of Name node
        A Name can occur on either the left or right side of an assignment.
        If it's on the left side the context is Store, and the Name is the
        variable name into which to store a value.  We push that variable name
        on the _store stack.
        If the Name is on the right side, e.g. as part of an expression,
        we look up the name in our params dict, and push the corresponding
        value on the _load stack.  If the name is not found, None is pushed
        on the _load stack.

        NB: The same instance of a Name can appear as different nodes in a AST,
        so nothing should be stored in the node as a node-specific attribute.
        """
        if self._reset_visited_states:
            return
        print("{}Name: {}".format(self._indentStr * self._indent, node.id))
        if isinstance(node.ctx, _ast.Store):
            print(f"Name is storing {node.id}")
            self._store.append(node.id)
        elif isinstance(node.ctx, _ast.Load):
            value = self._params.get(node.id)
            print(f"Name is loading {value} from {node.id}")
            self._load.append(value)
        else:
            print("visit_Name: ctx is unexpected type: {}".format(type(node.ctx)))
            setattr(node, 'kpf_completed', True)
    
    def visit_For(self, node):
        """
        Implement the For node

        """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            setattr(node, 'kpf_started', False)
            if hasattr(node, 'kpf_params'):
                delattr(node, 'kpf_params')
            self.visit(node.target)
            self.visit(node.iter)
            for subnode in node.body:
                self.visit(subnode)
            return
        print("{}For: {} in ".format(self._indentStr * self._indent, node.target.id))
        if not getattr(node, 'kpf_completed', False):
            if not getattr(node, 'kpf_started', False):
                params = {}
                storeQSizeBefore = len(self._store)
                self.visit(node.target)
                if self.awaiting_call_return:
                    return
                if len(self._store) > storeQSizeBefore:
                    target = self._store.pop()
                    params['target'] = target             
                loadQSizeBefore = len(self._load)
                self.visit(node.iter)
                args = deque()
                while len(self._load) > loadQSizeBefore:
                    args.appendleft(self._load.pop())
                # TODO: can this be made simpler?
                args_iter = iter(list(args))
                current_arg = next(args_iter)
                params['args_iter'] = args_iter
                params['current_arg'] = current_arg
                setattr(node, 'kpf_params', params)
                setattr(node, 'kpf_started', True)
            else:
                params = getattr(node, 'kpf_params', None)
                assert(params is not None)
                target = params.get('target')
                args_iter = params.get('args_iter')
                current_arg = params.get('current_arg')
            # TODO: how to loop?
            while True:
                self._params[target] = current_arg
                for subnode in node.body:
                    self.visit(subnode)
                    if self.awaiting_call_return:
                        return
                self.reset_visited_states(subnode)
                try:
                    current_arg = next(args_iter)
                    params['current_arg'] = current_arg
                except StopIteration:
                    break
            setattr(node, 'kpf_completed', True)

    
    def visit_Assign(self, node):
        """
        Assign one or more constant or calculated values to named variables
        The variable names come from the _store stack, while the values
        come from the _load stack.
        Calls to visit() may set self._awaiting_call_return, in which case
        we need to immediately return, and pick up where we left off later.
        """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            setattr(node, 'kpf_completed_targets', False)
            setattr(node, 'kpf_completed_values', False)
            if hasattr(node, 'kpf_storeQSizeBefore'):
                delattr(node, 'kpf_storeQSizeBefore')
            if hasattr(node, 'kpf_num_targets'):
                delattr(node, 'kpf_num_targets')
            for target in node.targets:
                self.visit(target)
            self.visit(node.value)
            return
        if not getattr(node, 'kpf_completed', False):
            print("{}Assign: ".format(self._indentStr * self._indent))
            self._indent += 1
            loadQSizeBefore = len(self._load)
            storeQSizeBefore = len(self._store)
            if not getattr(node, 'kpf_completed_targets', False):
                print(f"Assign: visiting targets, storeQSizeBefore is {storeQSizeBefore}")
                setattr(node, 'kpf_storeQSizeBefore', storeQSizeBefore)
                for target in node.targets:
                    self.visit(target)
                    if self.awaiting_call_return:
                        return
                print(f"Assign: len(_store) is now {len(self._store)}")
                num_store_targets = len(self._store[storeQSizeBefore:])
                setattr(node, "kpf_num_targets", num_store_targets)
                setattr(node, 'kpf_completed_targets', True)
            else:
                """
                # _store stack items should already be present, but need to know how many
                print(f"Assign: targets previously completed; storeQSizeBefore is {storeQSizeBefore}")
                targets = getattr(node, 'kpf_targets', None)
                print(f"Assign: targets is {targets}")
                for target in targets:
                    self._store.append(target)
                print(f"Assign: len(_store) is now {len(self._store)}")
                """
                num_store_targets = getattr(node, 'kpf_num_targets', 0)
            if not getattr(node, 'kpf_completed_values', False):
                print("{}Assign from:".format(self._indentStr * self._indent))
                self.visit(node.value)
                if self.awaiting_call_return:
                    return
                setattr(node, 'kpf_completed_values', True)
            print(f"Assign: len(store): {len(self._store)}, storeQSizeBefore: {storeQSizeBefore}")
            print(f"Assign: len(load): {len(self._load)}, loadQSizeBefore: {loadQSizeBefore}")
            while num_store_targets > 0 and len(self._load) > loadQSizeBefore:
                target = self._store.pop()
                self._params[target] = self._load.pop()
                num_store_targets -= 1
                print("{}Assign: {} <- {}".format(self._indentStr * self._indent, target, self._params[target]))
            while len(self._store) > storeQSizeBefore:
                print("{}Assign: unfilled target: {}".format(self._indentStr * self._indent, self._store.pop()))
            while len(self._load) > loadQSizeBefore:
                print("{}Assign: unused value: {}".format(self._indentStr * self._indent, self._load.pop()))
            self._indent -= 1
            setattr(node, 'kpf_completed', True)

    # UnaryOp and the unary operators
    
    def visit_UnaryOp(self, node):
        """ implement UnaryOp """
        if self._reset_visited_states:
            self.visit(node.operand)
            self.visit(node.op)
            return
        print("{}UnaryOp:".format(self._indentStr * self._indent))
        self.visit(node.operand)
        self.visit(node.op)

    # Unary Operators

    def visit_UAdd(self, node):
        """ implement UAdd """
        if self._reset_visited_states:
            return
        print("{}USub".format(self._indentStr * self._indent))
        if len(self._load) == 0:
            raise Exception("visit_UnaryOp: called with no argument")
        pass
        # it would be silly to do this:
        # self._load.append(+self._load.pop())

    def visit_USub(self, node):
        """ implement USub """
        if self._reset_visited_states:
            return
        print("{}USub".format(self._indentStr * self._indent))
        if len(self._load) == 0:
            raise Exception("visit_UnaryOp: called with no argument")
        self._load.append(-self._load.pop())

    def visit_UNot(self, node):
        """ implement USub """
        if self._reset_visited_states:
            return
        print("{}USub".format(self._indentStr * self._indent))
        if len(self._load) == 0:
            raise Exception("visit_UnaryOp: called with no argument")
        self._load.append(not self._load.pop())

    # BinOp and the binary operators

    def visit_BinOp(self, node):
        """
        BinOp
        """
        if self._reset_visited_states:
            self.visit(node.right)
            self.visit(node.left)
            self.visit(node.op)
            return
        print("{}BinOp:".format(self._indentStr * self._indent))
        self._indent += 1
        # right before left because they're being pushed on a stack, so left comes off first
        self.visit(node.right)
        self.visit(node.left)
        self.visit(node.op)
        self._indent -= 1

    # binary operators

    def visit_Add(self, node):
        """ implement the addition operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}Add")
        if len(self._load) < 2:
            raise Exception(f"Add called with insufficient number of arguments: {len(self._load)}")
        self._load.append(self._load.pop() + self._load.pop())

    def visit_Sub(self, node):
        """ implement the subtraction operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}Sub")
        if len(self._load) < 2:
            raise Exception(f"Sub called with insufficient number of arguments: {len(self._load)}")
        self._load.append(self._load.pop() - self._load.pop())
    
    def visit_Mult(self, node):
        """ implement the multiplication operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}Mult")
        if len(self._load) < 2:
            raise Exception(f"Mult called with insufficient number of arguments: {self._load.qsize()}")
        self._load.append(self._load.pop() * self._load.pop())
    
    def visit_Div(self, node):
        """ implement the division operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}Div")
        if len(self._load) < 2:
            raise Exception(f"Div called with insufficient number of arguments: {len(self._load)}")
        self._load.append(self._load.pop() / self._load.pop())
    
    # Comparison operators

    def visit_Eq(self, node):
        """ implement Eq comparison operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}Eq")
        if len(self._load) < 2:
            raise Exception(f"Eq called with less than two arguments: {self._load.qsize()}")
        self._load.append(self._load.pop() == self._load.pop())
    
    def visit_NotEq(self, node):
        """ implement NotEq comparison operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}NotEq")
        if len(self._load) < 2:
            raise Exception(f"NotEq called with less than two arguments: {len(self._load)}")
        self._load.append(self._load.pop() != self._load.pop())
    
    def visit_Lt(self, node):
        """ implement Lt comparison operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}Lt")
        if len(self._load) < 2:
            raise Exception(f"Lt called with less than two arguments: {len(self._load)}")
        self._load.append(self._load.pop() < self._load.pop())
    
    def visit_LtE(self, node):
        """ implement LtE comparison operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}LtE")
        if len(self._load) < 2:
            raise Exception(f"LtE called with less than two arguments: {len(self._load)}")
        self._load.append(self._load.pop() <= self._load.pop())
    
    def visit_Gt(self, node):
        """ implement Gt comparison operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}Gt")
        if len(self._load) < 2:
            raise Exception(f"Gt called with less than two arguments: {self._load.qsize()}")
        self._load.append(self._load.pop() > self._load.pop())
    
    def visit_GtE(self, node):
        """ implement GtE comparison operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}GtE")
        if len(self._load) < 2:
            raise Exception(f"GtE called with less than two arguments: {len(self._load)}")
        self._load.append(self._load.pop() >= self._load.pop())
    
    def visit_Is(self, node):
        """ implement Lt comparison operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}Is")
        if len(self._load) < 2:
            raise Exception(f"Is called with less than two arguments: {len(self._load)}")
        self._load.append(self._load.pop() is self._load.pop())
    
    def visit_IsNot(self, node):
        """ implement Lt comparison operator """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}IsNot")
        if len(self._load) < 2:
            raise Exception(f"IsNot called with less than two arguments: {len(self._load)}")
        self._load.append(not (self._load.pop() is self._load.pop()))
    
    # TODO: implement visit_In and visit_NotIn.  Depends on support for Tuple and maybe others

    def visit_Call(self, node):
        """
        Implement function call
        The arguments are pulled from the _load stack into a deque.
        Targets are put on the _store stack.
        TODO: We need some mechanism for getting the results of the call and putting
        them in the _params dict under the keywords from the _store stack.
        Maybe a _call_pending Bool and a number of results expected?
        """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            for arg in node.args:
                self.visit(arg)
            return
        if not getattr(node, 'kpf_completed', False):
            print(f"{self._indentStr * self._indent}Call: {node.func.id}")
            if not self.returning_from_call:
                loadSizeBefore = len(self._load)
                for arg in node.args:
                    self.visit(arg)
                func_args = list()
                while len(self._load) > loadSizeBefore:
                    foo = self._load.pop()
                    print(f"Call: processing arg {foo}")
                    func_args.append(foo)
                print(f"Call: func_args: {func_args}")
                pipe_args = KpfPipelineArgs(self, self.tree, func_args)
                print(f"{self._indentStr * self._indent}Call: {node.func.id}, args: {pipe_args}")
                
                event = (node.func.id, None, "resume_Call")
                #TODO the below will need to be replaced by something that calls push_event
                self.action = Action(event, pipe_args)
                self.output = self._prims[node.func.id](self.action, self.context)
                #
                self.awaiting_call_return = True
                return
            else:
                self.returning_from_call = False
                print(f"Call: returning, output is {self.action.output}")
                for output in self.call_output:
                    self._load.append(output)
                self.call_output = None
            setattr(node, 'kpf_completed', True)

    
    def visit_Compare(self, node):
        """
        Implement Compare as follows:
        visiting "left" and "comparators" puts values on the _load stack.
        visiting "ops" evaluates some comparison operator, and puts the result
        on the _load stack as a Bool.
        """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            for item in node.comparators:
                self.visit(item)
            self.visit(node.left)
            for op in node.ops:
                self.visit(op)
            return
        if not getattr(node, 'kpf_completed', False):
            print("{}Compare".format(self._indentStr * self._indent))
            loadQSizeBefore = len(self._load)
            # comparators before left because they're going on a stack, so left can be pulled first
            for item in node.comparators:
                self.visit(item)
            self.visit(node.left)
            for op in node.ops:
                self.visit(op)
            print("{}Compare changed load qsize by {}".format(
                self._indentStr * self._indent,
                len(self._load)-loadQSizeBefore))
            setattr(node, 'kpf_completed', True)

    def visit_If(self, node):
        """
        Implementation of If
        Evaluate the test and visit one of the two branches, body or orelse.
        """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            setattr(node, 'kpf_completed_test', False)
            if hasattr(node, 'kpf_boolResult'):
                delattr(node, 'kpf_boolResult')
            self.visit(node.test)
            for item in node.body:
                self.visit(item)
            for item in node.orelse:
                self.visit(item)
            return
        if not getattr(node, 'kpf_completed', False):
            print("{}If".format(self._indentStr * self._indent))
            self._indent += 1
            if not getattr(node, 'kpf_completed_test', False):
                print("{}test: ".format(self._indentStr * self._indent))
                loadQSizeBefore = len(self._load)
                self.visit(node.test)
                if len(self._load) <= loadQSizeBefore:
                    raise Exception("visit_If: test didn't push a result on the _load stack")
                boolResult = self._load.pop()
                setattr(node, 'kpf_boolResult', boolResult)
                setattr(node, 'kpf_completed_test', True)
            else:
                boolResult = getattr(node, 'kpf_boolResult')
            if boolResult:
                print("{}pushing and visiting Ifso: ".format(self._indentStr * self._indent))
                for item in node.body:
                    self.visit(item)
                    if self.awaiting_call_return:
                        return
            else:
                print("{}pushing and visiting Else:".format(self._indentStr * self._indent))
                for item in node.orelse:
                    self.visit(item)
                    if self.awaiting_call_return:
                        return
            self._indent -= 1
            setattr(node, 'kpf_completed', True)

    def visit_List(self, node):
        """
        List node
        """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            for elt in node.elts:
                self.visit(elt)
            return
        print("{}List".format(self._indentStr * self._indent))
        if not getattr(node, "kpf_completed", False):
            for elt in node.elts:
                self.visit(elt)
            setattr(node, "kpf_completed", True)
    
    def visit_Tuple(self, node):
        """
        Tuple node
        """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            return
        print("{}Tuple".format(self._indentStr * self._indent))
        if not getattr(node, "kpf_completed", False):
            for elt in node.elts:
                self.visit(elt)
            setattr(node, "kpf_completed", True)
        
    def visit_Num(self, node):
        """
        Num
        implement numeric constant by putting it on the _load stack

        NB: An instance of Num can appear as different nodes in the same AST,
        so we can't store node specific information as an attribute.
        """
        if self._reset_visited_states:
            return
        print("{}Num: {}".format(self._indentStr * self._indent, node.n))
        # ctx of Num is always Load
        self._load.append(node.n)

    def visit_Str(self, node):
        """
        Str node
        TODO: I'm not sure what to do with a multiline comment expressed as Str
        """
        if self._reset_visited_states:
            return
        print(f"{self._indentStr * self._indent}Str: {node.s}")
        # ctx of Str is always Load
        self._load.append(node.s)
    
    def visit_Expr(self, node):
        """
        Expr node
        """
        if self._reset_visited_states:
            setattr(node, 'kpf_completed', False)
            self.visit(node.value)
            return
        if not getattr(node, 'kpf_completed', False):
            self.visit(node.value)
            if self.awaiting_call_return:
                return
            setattr(node, 'kpf_complted', True)

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        print("generic_visit: got {}".format(type(node)))
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, _ast.AST):
                        self.visit(item)
            elif isinstance(value, _ast.AST):
                self.visit(value)
    
    def reset_visited_states(self, node):
        """
        Resets kpf_completed and other attributes of this and all subnodes,
        e.g. so that a for loop can iterate with a fresh start.
        """
        self._reset_visited_states = True
        self.awaiting_call_return = False
        self.returning_from_call = False
        self.call_output = None
        self.visit(node)
        self._load.clear()
        self._store.clear()
        self._reset_visited_states = False


class FauxFramework():
    """
    FauxFramework is a simple replacement for the Keck DRP Framework
    The purpose is to work out how to integrate our AST=based pipeline
    into such a framework.
    """

    _event_queue = Queue()

    def __init__(self, v):
        self._v = v
    
    def queue_push(self, item):
        self._event_queue.put(item)
    
    def execute(self):
        item = self._event_queue.get()

# reentry after call

def resume_Call(action: Action, context: ProcessingContext):
    # pick up the recipe processing where we left off
    v = action.args.visitor
    t = action.args.tree
    v.returning_from_call = True
    v.awaiting_call_return = False
    v.call_output = action.args.args # framework put previous output here
    v.visit(t)
    return KpfPipelineArgs(action.args.visitor, action.args.tree, ())