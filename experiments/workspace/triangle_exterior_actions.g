# Enumerate degree-60 transitive actions faithful on twenty blocks of size 3.
# Run in a temporary directory. Each line records the source group, one block
# and the generators on 60 points, using zero-based labels.
EmitExteriorActions := function(groupNumber, output)
    local group, blockStab, target, quotient, pointStab, cosets, action,
          base, block, generators, images, record, count;
    group := TransitiveGroup(20, groupNumber);
    blockStab := Stabilizer(group, 1);
    if Size(blockStab) mod 3 <> 0 then return 0; fi;
    count := 0;
    for target in [AlternatingGroup(3), SymmetricGroup(3)] do
        for quotient in GQuotients(blockStab, target) do
            pointStab := PreImage(quotient, Stabilizer(target, 1));
            cosets := RightCosets(group, pointStab);
            Assert(0, Length(cosets) = 60);
            action := ActionHomomorphism(group, cosets, OnRight);
            base := Position(cosets, RightCoset(pointStab, One(group)));
            block := Orbit(Image(action, blockStab), base);
            Assert(0, Length(block) = 3);
            generators := List(GeneratorsOfGroup(group), g -> Image(action, g));
            images := List(generators, g -> List([1..60], i -> i^g - 1));
            record := Concatenation([groupNumber, count, Length(generators)],
                                    block - 1, Concatenation(images));
            PrintTo(output, JoinStringsWithSeparator(List(record, String), " "), "\n");
            count := count + 1;
        od;
    od;
    return count;
end;

if NrTransitiveGroups(20) <> 1117 then Error("degree-20 catalog mismatch"); fi;
output := OutputTextFile("triangle-exterior.actions", false);;
SetPrintFormattingStatus(output, false);
total := Sum([1..1117], i -> EmitExteriorActions(i, output));;
CloseStream(output);
Assert(0, total = 912);
Print("Degree-20 groups: 1117. Marked degree-60 actions: ", total, ".\n");
QUIT;
